from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base, db


class UserTeam(db.Model):
    """
    Represents the association between a user and a team.

    Attributes:
        user_id (int): The unique identifier of the user.
        team_id (int): The unique identifier of the team.
        role (str): The role of the user in the team.
        joined_at (datetime): The timestamp when the user joined the team.
        user (relationship): The user associated with the team.
        team (relationship): The team associated with the user.
    """

    __tablename__ = "user_teams"

    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey("teams.team_id"), primary_key=True)
    role = db.Column(db.String, nullable=False, default="member")
    joined_at = db.Column(db.DateTime, default=datetime.now)

    user = db.relationship("User", back_populates="teams")
    team = db.relationship("Team", back_populates="members")

    def __repr__(self) -> str:
        """
        Returns a string representation of the UserTeam object.

        Returns:
            str: A string representation of the UserTeam object.
        """
        return f"<UserTeam(user_id={self.user_id}, team_id={self.team_id}, role={self.role}, joined_at={self.joined_at})>"
