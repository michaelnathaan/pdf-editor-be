from sqlalchemy import Column, String, BigInteger, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class EditSession(Base):
    __tablename__ = "edit_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_id = Column(UUID(as_uuid=True), ForeignKey("files.id", ondelete="CASCADE"), nullable=False)
    session_token = Column(String(255), nullable=False, unique=True)
    status = Column(String(20), default="active")  # active, completed, expired
    
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    last_activity_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    edited_file_path = Column(String(500), nullable=True)
    edited_file_size = Column(BigInteger, nullable=True)
    
    permissions = Column(JSONB, default={"can_edit": True, "can_download": True})
    
    callback_url = Column(String(500), nullable=True)
    callback_status = Column(String(20), nullable=True)  # pending, success, failed
    
    # Relationships
    file = relationship("File", back_populates="sessions")
    operations = relationship("EditOperation", back_populates="session", cascade="all, delete-orphan")
    images = relationship("SessionImage", back_populates="session", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<EditSession(id={self.id}, status={self.status})>"