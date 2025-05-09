from datetime import datetime
from backend.database import db, Base
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship

class Team(Base):
    __tablename__ = "teams"
# - Attributes:
    team_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
# - Relationships:
    members = relationship("UserTeam", back_populates="team", cascade="all, delete")
    project = relationship("Project", back_populates="team", cascade="all, delete")

# - Validation
    def is_valid(self):
        if not self.name or not self.name.strip():
            return False
        return True


