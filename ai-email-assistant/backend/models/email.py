from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database.db import Base

class EmailRecord(Base):
    __tablename__ = "email_records"

    id = Column(Integer, primary_key=True, index=True)
    subject = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    tone = Column(String(50), nullable=True)
    recipient = Column(String(255), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Optional user association
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user = relationship("User", back_populates="emails")

    def __repr__(self):
        return f"<EmailRecord(subject='{self.subject}', user_id={self.user_id})>"