import os
import smtplib
import ssl
from email import encoders
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate, make_msgid
from typing import Dict, List, Optional, Union
from jinja2 import Template
from retry import retry
import dns.resolver
from prometheus_client import Counter, Histogram

# Metrics
EMAIL_SEND_ATTEMPTS = Counter(
    'email_send_attempts_total',
    'Total number of email send attempts',
    ['status']
)
EMAIL_SEND_DURATION = Histogram(
    'email_send_duration_seconds',
    'Time taken to send emails',
    ['status']
)

class EmailError(Exception):
    """Base exception for email-related errors."""
    pass

class SMTPConnectionError(EmailError):
    """SMTP connection or authentication errors."""
    pass

class InvalidRecipientError(EmailError):
    """Invalid or non-existent recipient email."""
    pass

class AttachmentError(EmailError):
    """Errors related to email attachments."""
    pass

class EmailTemplate:
    """Email template manager using Jinja2."""
    
    def __init__(self, template_dir: str = None):
        self.template_dir = template_dir or os.path.join(
            os.path.dirname(__file__), 
            "../templates/email"
        )
    
    def render(self, template_name: str, context: Dict) -> str:
        """Render a template with given context."""
        template_path = os.path.join(self.template_dir, template_name)
        try:
            with open(template_path, 'r') as f:
                template = Template(f.read())
                return template.render(**context)
        except Exception as e:
            raise EmailError(f"Template rendering failed: {str(e)}")

class EmailSender:
    """Enhanced email sender with support for HTML, attachments, and templates."""
    
    def __init__(
        self,
        smtp_host: str = "smtp.gmail.com",
        smtp_port: int = 465,
        use_tls: bool = True,
        max_retries: int = 3,
        retry_delay: int = 5
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.use_tls = use_tls
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.template_manager = EmailTemplate()
    
    def _create_message(
        self,
        sender: str,
        recipients: Union[str, List[str]],
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        cc: Optional[Union[str, List[str]]] = None,
        bcc: Optional[Union[str, List[str]]] = None,
        attachments: Optional[List[str]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> MIMEMultipart:
        """Create a MIME message with all components."""
        msg = MIMEMultipart('alternative')
        
        # Basic headers
        msg['From'] = sender
        msg['To'] = recipients if isinstance(recipients, str) else ", ".join(recipients)
        msg['Subject'] = subject
        msg['Date'] = formatdate()
        msg['Message-ID'] = make_msgid()
        
        # Optional headers
        if cc:
            msg['Cc'] = cc if isinstance(cc, str) else ", ".join(cc)
        if bcc:
            msg['Bcc'] = bcc if isinstance(bcc, str) else ", ".join(bcc)
        if headers:
            for key, value in headers.items():
                msg[key] = value
        
        # Add plain text and HTML versions
        msg.attach(MIMEText(body, 'plain'))
        if html_body:
            msg.attach(MIMEText(html_body, 'html'))
        
        # Add attachments
        if attachments:
            for attachment_path in attachments:
                try:
                    with open(attachment_path, 'rb') as f:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(f.read())
                        encoders.encode_base64(part)
                        
                        filename = os.path.basename(attachment_path)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename="{filename}"'
                        )
                        msg.attach(part)
                except Exception as e:
                    raise AttachmentError(f"Failed to attach {attachment_path}: {str(e)}")
        
        return msg
    
    def _verify_recipient(self, email: str) -> bool:
        """Verify recipient email domain has valid MX records."""
        try:
            domain = email.split('@')[1]
            return bool(dns.resolver.resolve(domain, 'MX'))
        except Exception:
            return False
    
    @retry(exceptions=(SMTPConnectionError,), tries=3, delay=5)
    def send_email(
        self,
        sender: str,
        password: str,
        recipients: Union[str, List[str]],
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        cc: Optional[Union[str, List[str]]] = None,
        bcc: Optional[Union[str, List[str]]] = None,
        attachments: Optional[List[str]] = None,
        template_name: Optional[str] = None,
        template_context: Optional[Dict] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Send an email with enhanced features and error handling.
        
        Args:
            sender: Sender's email address
            password: Sender's email password or app password
            recipients: Single recipient or list of recipients
            subject: Email subject line
            body: Plain text email body
            html_body: Optional HTML version of the email
            cc: Optional CC recipients
            bcc: Optional BCC recipients
            attachments: Optional list of file paths to attach
            template_name: Optional template file name to use
            template_context: Context data for template rendering
            headers: Optional additional email headers
            
        Raises:
            SMTPConnectionError: SMTP connection or authentication failed
            InvalidRecipientError: Invalid recipient email
            AttachmentError: Attachment processing failed
            EmailError: Other email-related errors
        """
        try:
            with EMAIL_SEND_DURATION.labels(status='total').time():
                # Use template if specified
                if template_name:
                    if not template_context:
                        template_context = {}
                    body = self.template_manager.render(template_name, template_context)
                
                # Convert single recipient to list
                if isinstance(recipients, str):
                    recipients = [recipients]
                
                # Verify recipients
                for recipient in recipients:
                    if not self._verify_recipient(recipient):
                        raise InvalidRecipientError(
                            f"Invalid recipient email: {recipient}"
                        )
                
                # Create message
                msg = self._create_message(
                    sender=sender,
                    recipients=recipients,
                    subject=subject,
                    body=body,
                    html_body=html_body,
                    cc=cc,
                    bcc=bcc,
                    attachments=attachments,
                    headers=headers
                )
                
                # Set up SSL context
                context = ssl.create_default_context()
                
                # Connect and send
                try:
                    if self.use_tls:
                        smtp = smtplib.SMTP(self.smtp_host, self.smtp_port)
                        smtp.starttls(context=context)
                    else:
                        smtp = smtplib.SMTP_SSL(
                            self.smtp_host,
                            self.smtp_port,
                            context=context
                        )
                    
                    smtp.login(sender, password)
                    
                    # Get all recipients
                    all_recipients = recipients
                    if cc:
                        all_recipients.extend(cc if isinstance(cc, list) else [cc])
                    if bcc:
                        all_recipients.extend(bcc if isinstance(bcc, list) else [bcc])
                    
                    smtp.send_message(msg)
                    smtp.quit()
                    
                    EMAIL_SEND_ATTEMPTS.labels(status='success').inc()
                    
                except smtplib.SMTPException as e:
                    EMAIL_SEND_ATTEMPTS.labels(status='failure').inc()
                    raise SMTPConnectionError(f"SMTP error: {str(e)}")
                
        except EmailError:
            # Re-raise email-specific errors
            raise
        except Exception as e:
            # Wrap other errors
            raise EmailError(f"Email send failed: {str(e)}")
    
    def send_template_email(
        self,
        sender: str,
        password: str,
        recipients: Union[str, List[str]],
        template_name: str,
        template_context: Dict,
        **kwargs
    ) -> None:
        """
        Convenience method to send an email using a template.
        
        Additional kwargs are passed to send_email().
        """
        # Render template
        body = self.template_manager.render(template_name, template_context)
        
        # Send email with rendered template
        self.send_email(
            sender=sender,
            password=password,
            recipients=recipients,
            body=body,
            template_name=template_name,
            template_context=template_context,
            **kwargs
        )