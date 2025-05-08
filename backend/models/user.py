from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base


class User(Base):
    """
    Represents a user in the system.

    Attributes:
        user_id (int): The unique identifier for the user.
        username (str): The user's username.
        email (str): The user's email address.
        password_hash (str): The hashed password for the user.
        first_name (str): The user's first name.
        last_name (str): The user's last name.
        created_at (datetime): The timestamp when the user was created.
        last_active (datetime): The timestamp of the user's last activity.
        profile_picture (str, optional): The URL or path to the user's profile picture.
        teams (relationship): The teams the user is a member of.
    """

    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    last_active = Column(DateTime, default=datetime.now)
    profile_picture = Column(String, nullable=True)

    teams = relationship("UserTeam", back_populates="user")

    def __repr__(self) -> str:
        """
        Returns a string representation of the User object.

        Returns:
            str: A string representation of the user object.
        """
        return f"<User(id={self.user_id}, email={self.email}, password_hash={self.password_hash}, first_name={self.first_name}, last_name={self.last_name})>"
