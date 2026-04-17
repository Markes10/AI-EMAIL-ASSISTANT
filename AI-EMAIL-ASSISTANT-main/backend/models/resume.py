from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database.db import Base

class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)  # Parsed text from resume
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    # Optional user association
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user = relationship("User", back_populates="resumes")

    # Optional job description link
    job_description = Column(Text, nullable=True)
    matched_score = Column(Integer, nullable=True)  # NLP-based match score

    def __repr__(self):
        return f"<Resume(filename='{self.filename}', user_id={self.user_id})>"