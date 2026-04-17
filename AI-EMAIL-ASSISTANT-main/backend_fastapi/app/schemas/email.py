from pydantic import BaseModel, EmailStr
from typing import Optional


class EmailGenerateRequest(BaseModel):
    subject: str
    context: str
    tone: Optional[str] = 'Formal'
    recipient_name: Optional[str] = None
    recipient: Optional[EmailStr] = None
    cc: Optional[str] = None
    bcc: Optional[str] = None
    use_gpt: Optional[bool] = True


class EmailOut(BaseModel):
    id: str
    subject: str
    body: str
    tone: Optional[str]
    recipient: Optional[str]
