from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class EditOperation(Base):
    __tablename__ = "edit_operations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("edit_sessions.id", ondelete="CASCADE"), nullable=False)
    operation_order = Column(Integer, nullable=False)
    operation_type = Column(String(50), nullable=False)  # add_image, move_image, resize_image, delete_image, rotate_image
    operation_data = Column(JSONB, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("EditSession", back_populates="operations")
    
    __table_args__ = (
        UniqueConstraint('session_id', 'operation_order', name='uq_session_operation_order'),
    )
    
    def __repr__(self):
        return f"<EditOperation(id={self.id}, type={self.operation_type}, order={self.operation_order})>"