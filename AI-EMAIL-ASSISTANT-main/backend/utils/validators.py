import re
from typing import Dict, List, Tuple, Union
from email_validator import validate_email, EmailNotValidError
from langdetect import detect
import magic  # For MIME type detection

class ValidationError(Exception):
    """Custom exception for validation errors with detailed messages."""
    def __init__(self, message: str, code: str, details: Dict = None):
        super().__init__(message)
        self.code = code
        self.details = details or {}

def validate_email_address(email: str) -> Tuple[bool, Union[str, None]]:
    """
    Validate email format using email-validator library.
    Checks for:
    - Proper format
    - Valid domain
    - Common typos
    - Disposable email providers
    
    Returns:
        Tuple[bool, Union[str, None]]: (is_valid, error_message)
    """
    try:
        # Normalize and validate the email
        valid = validate_email(email)
        normalized_email = valid.email
        
        # Check for disposable email providers
        domain = normalized_email.split('@')[1].lower()
        disposable_domains = {"temp-mail.org", "tempmail.com", "throwawaymail.com"}
        if domain in disposable_domains:
            return False, "Disposable email addresses are not allowed"
        
        return True, None
    except EmailNotValidError as e:
        return False, str(e)

def validate_password_strength(password: str) -> Tuple[bool, Union[str, Dict]]:
    """
    Comprehensive password strength validation.
    
    Returns:
        Tuple[bool, Union[str, Dict]]: (is_valid, error_message_or_strength_info)
    """
    MIN_LENGTH = 8
    MAX_LENGTH = 128
    
    checks = {
        'length': len(password) >= MIN_LENGTH and len(password) <= MAX_LENGTH,
        'uppercase': bool(re.search(r'[A-Z]', password)),
        'lowercase': bool(re.search(r'[a-z]', password)),
        'digits': bool(re.search(r'\d', password)),
        'special': bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password)),
        'no_whitespace': not bool(re.search(r'\s', password)),
        'no_common': not any(common in password.lower() 
                           for common in ['password', '123456', 'qwerty'])
    }
    
    # Calculate password strength
    strength_score = sum(1 for check in checks.values() if check)
    strength_level = {
        7: "strong",
        6: "good",
        5: "moderate",
        4: "weak",
    }.get(strength_score, "very weak")
    
    if all(checks.values()):
        return True, {
            'strength': strength_level,
            'score': strength_score,
            'length': len(password)
        }
    
    # Generate specific error messages
    errors = []
    if not checks['length']:
        errors.append(f"Password must be between {MIN_LENGTH} and {MAX_LENGTH} characters")
    if not checks['uppercase']:
        errors.append("Include at least one uppercase letter")
    if not checks['lowercase']:
        errors.append("Include at least one lowercase letter")
    if not checks['digits']:
        errors.append("Include at least one number")
    if not checks['special']:
        errors.append("Include at least one special character")
    if not checks['no_whitespace']:
        errors.append("Password cannot contain whitespace")
    if not checks['no_common']:
        errors.append("Password is too common")
    
    return False, {
        'strength': strength_level,
        'score': strength_score,
        'errors': errors
    }

def validate_tone(tone: str, allowed_tones: List[str]) -> Tuple[bool, Union[str, None]]:
    """
    Validate tone with fuzzy matching and suggestions.
    
    Returns:
        Tuple[bool, Union[str, None]]: (is_valid, error_message)
    """
    if not tone:
        return False, "Tone cannot be empty"
    
    tone_clean = tone.strip().capitalize()
    
    # Exact match
    if tone_clean in allowed_tones:
        return True, None
    
    # Fuzzy match for suggestions
    import difflib
    matches = difflib.get_close_matches(tone_clean, allowed_tones, n=3, cutoff=0.6)
    
    if matches:
        suggestion_msg = f"Invalid tone. Did you mean: {', '.join(matches)}?"
        return False, suggestion_msg
    
    return False, f"Invalid tone. Allowed options are: {', '.join(allowed_tones)}"

def validate_file(file_path: str, allowed_types: List[str], 
                max_size_mb: float = 10) -> Tuple[bool, Union[str, None]]:
    """
    Comprehensive file validation.
    
    Args:
        file_path: Path to the file
        allowed_types: List of allowed MIME types
        max_size_mb: Maximum file size in MB
        
    Returns:
        Tuple[bool, Union[str, None]]: (is_valid, error_message)
    """
    try:
        # Check file existence
        import os
        if not os.path.exists(file_path):
            return False, "File does not exist"
        
        # Check file size
        size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if size_mb > max_size_mb:
            return False, f"File size exceeds {max_size_mb}MB limit"
        
        # Check MIME type
        mime_type = magic.from_file(file_path, mime=True)
        if mime_type not in allowed_types:
            return False, (f"Invalid file type: {mime_type}. "
                         f"Allowed types: {', '.join(allowed_types)}")
        
        # For documents, check if file is not corrupted
        if mime_type in ['application/pdf', 'application/msword']:
            # Try to open and read first few bytes
            with open(file_path, 'rb') as f:
                f.read(512)
        
        return True, None
    
    except Exception as e:
        return False, f"File validation error: {str(e)}"

def validate_text_content(text: str, max_length: int = None, 
                        min_length: int = None,
                        allowed_languages: List[str] = None) -> Tuple[bool, Union[str, None]]:
    """
    Validate text content with length and language checks.
    
    Args:
        text: The text to validate
        max_length: Maximum allowed length (optional)
        min_length: Minimum required length (optional)
        allowed_languages: List of allowed language codes (optional)
    
    Returns:
        Tuple[bool, Union[str, None]]: (is_valid, error_message)
    """
    if not text or not text.strip():
        return False, "Text cannot be empty"
    
    text_clean = text.strip()
    
    # Length validation
    if max_length and len(text_clean) > max_length:
        return False, f"Text exceeds maximum length of {max_length} characters"
    
    if min_length and len(text_clean) < min_length:
        return False, f"Text must be at least {min_length} characters"
    
    # Language validation
    if allowed_languages:
        try:
            detected_lang = detect(text_clean)
            if detected_lang not in allowed_languages:
                return False, (f"Text language '{detected_lang}' not allowed. "
                             f"Supported languages: {', '.join(allowed_languages)}")
        except Exception:
            return False, "Could not detect text language"
    
    return True, None

def sanitize_input(text: str, allow_html: bool = False) -> str:
    """
    Sanitize input text to prevent XSS and other injection attacks.
    """
    if not allow_html:
        # Remove HTML tags
        text = re.sub(r'<[^>]*>', '', text)
    
    # Remove potentially dangerous characters
    text = re.sub(r'[^\w\s@.,!?-]', '', text)
    
    # Normalize whitespace
    text = ' '.join(text.split())
    
    return text.strip()

def validate_json_structure(data: Dict, required_fields: List[str], 
                          field_types: Dict[str, type]) -> Tuple[bool, Union[str, None]]:
    """
    Validate JSON structure against a schema.
    
    Args:
        data: JSON data to validate
        required_fields: List of required field names
        field_types: Dictionary mapping field names to their expected types
    
    Returns:
        Tuple[bool, Union[str, None]]: (is_valid, error_message)
    """
    # Check required fields
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return False, f"Missing required fields: {', '.join(missing_fields)}"
    
    # Validate field types
    for field, expected_type in field_types.items():
        if field in data and not isinstance(data[field], expected_type):
            return False, (f"Field '{field}' must be of type "
                         f"{expected_type.__name__}")
    
    return True, None