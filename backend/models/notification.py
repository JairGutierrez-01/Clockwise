from datetime import datetime
from backend.database import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship

class Notification(Base):

    __tablename__ = "notifications"

#   Attributes
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    message = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    type = Column(String, nullable=False)
    is_read = Column(Boolean, default=False)

#   Relationships
    user = relationship("User", back_populates="notifications")
    project = relationship("Project", back_populates="notifications")
