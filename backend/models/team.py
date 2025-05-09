from datetime import datetime
from backend.database import db, Base
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship


class Team(db.Model):
    __tablename__ = "teams"
    # - Attributes:
    team_id = db.Column(db.Integer, primary_key=True, index=True)
    name = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    # - Relationships:
    members = db.relationship("UserTeam", back_populates="team", cascade="all, delete")
    project = db.relationship("Project", back_populates="team", cascade="all, delete")

    # - Validation
    def is_valid(self):
        if not self.name or not self.name.strip():
            return False
        return True
