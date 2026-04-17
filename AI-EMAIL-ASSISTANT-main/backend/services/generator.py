from transformers import pipeline
import openai
from typing import Optional
from datetime import datetime
from config import config
from utils.metrics import email_generation_count

# Initialize Hugging Face pipeline for backup
hf_generator = pipeline(
    task=config.HF_TASK,
    model=config.HF_MODEL,
    device=-1  # Use CPU; set to 0 for GPU if available
)

TONE_DESCRIPTIONS = {
    "Formal": "professional and business-appropriate",
    "Friendly": "warm and approachable while maintaining professionalism",
    "Persuasive": "convincing and compelling while being respectful",
    "Apologetic": "sincere and remorseful while maintaining professionalism",
    "Assertive": "confident and direct while remaining professional"
}

TONE_EXAMPLES = {
    "Formal": {
        "greeting": "Dear [Name],",
        "closing": "Best regards,"
    },
    "Friendly": {
        "greeting": "Hi [Name],",
        "closing": "Thanks and best wishes,"
    },
    "Persuasive": {
        "greeting": "Dear [Name],",
        "closing": "Looking forward to your positive response,"
    },
    "Apologetic": {
        "greeting": "Dear [Name],",
        "closing": "Sincerely apologizing,"
    },
    "Assertive": {
        "greeting": "Dear [Name],",
        "closing": "Best regards,"
    }
}

def generate_email_with_gpt(subject: str, context: str, tone: str, recipient_name: Optional[str] = None) -> str:
    """
    Generate email using OpenAI's GPT model with fallback to Hugging Face.
    """
    try:
        tone_desc = TONE_DESCRIPTIONS.get(tone, "professional")
        greeting = TONE_EXAMPLES[tone]["greeting"].replace("[Name]", recipient_name or "")
        
        prompt = f"""Generate a {tone_desc} email based on the following:

Subject: {subject}
Context: {context}

Requirements:
- Use {tone.lower()} tone
- Be clear and concise
- Follow proper email structure
- Include appropriate greeting and closing
- Maintain professional language
- Address key points from the context

Email structure:
1. Start with: "{greeting if recipient_name else 'Dear Sir/Madam,'}"
2. Introduction paragraph
3. Main content paragraphs
4. Closing paragraph
5. End with: "{TONE_EXAMPLES[tone]['closing']}"
"""

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a professional email writing assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        email_generation_count.inc()  # Increment metric
        return response.choices[0].message.content.strip()

    except Exception as e:
        # Fallback to Hugging Face
        return generate_email_with_huggingface(subject, context, tone)

def generate_email_with_huggingface(subject: str, context: str, tone: str) -> str:
    """
    Fallback email generation using Hugging Face model.
    """
    prompt = f"""Write a {tone.lower()} email.
Subject: {subject}
Details: {context}
Make it clear, professional, and well-structured.
Use proper email format with greeting and closing."""

    try:
        result = hf_generator(
            prompt,
            max_length=500,
            do_sample=True,
            temperature=0.7,
            top_p=0.9,
            repetition_penalty=1.2
        )
        email_generation_count.inc()  # Increment metric
        return result[0]['generated_text'].strip()
    except Exception as e:
        return f"Error generating email: {str(e)}"

def generate_email(
    subject: str,
    context: str,
    tone: str = "Formal",
    recipient_name: Optional[str] = None,
    use_gpt: bool = True
) -> str:
    """
    Main email generation function.

    Returns the generated email body as a plain string. Metadata is intentionally
    omitted here to keep the caller interfaces simple (routes and frontend
    expect a string body).
    """
    # Generate email content (string)
    content = (
        generate_email_with_gpt(subject, context, tone, recipient_name)
        if use_gpt else
        generate_email_with_huggingface(subject, context, tone)
    )

    # Increment metric
    try:
        email_generation_count.inc()
    except Exception:
        pass

    return content