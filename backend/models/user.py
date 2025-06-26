from datetime import datetime

from flask_login import UserMixin

from backend.database import db


class User(db.Model, UserMixin):
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
        project (relationship): The projects the user is associated with.
        assigned_task (relationship): The tasks assigned to the user.
        admin_tasks (relationship): Tasks where the user is the admin (creator) in a team project.
        member_tasks (relationship): Tasks assigned to the user as a team member.
        time_entries (relationship): The time entries related to the user.
        notifications (relationship): The notifications related to the user.
        categories (relationship): The categories the user has created.
    """

    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key=True, index=True)
    username = db.Column(db.String, unique=True, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password_hash = db.Column(db.String, nullable=False)
    first_name = db.Column(db.String, nullable=False)
    last_name = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    last_active = db.Column(db.DateTime, default=datetime.now)
    profile_picture = db.Column(db.String, nullable=True)

    teams = db.relationship("UserTeam", back_populates="user")
    project = db.relationship("Project", back_populates="user")
    assigned_task = db.relationship(
        "Task", foreign_keys="Task.user_id", back_populates="assigned_user"
    )
    admin_tasks = db.relationship(
        "Task", foreign_keys="Task.admin_id", back_populates="admin"
    )
    member_tasks = db.relationship(
        "Task", foreign_keys="Task.member_id", back_populates="member"
    )
    time_entries = db.relationship("TimeEntry", back_populates="user")
    notifications = db.relationship("Notification", back_populates="user")
    categories = db.relationship("Category", back_populates="user")

    def get_id(self):
        """
        Gets the string representation of the user ID.

        Returns:
            str: The user ID as a string.
        """
        return str(self.user_id)

    def __repr__(self) -> str:
        """
        Returns a string representation of the User object.

        Returns:
            str: A string representation of the user object.
        """
        return f"<User(id={self.user_id}, username={self.username}, email={self.email}, password_hash={self.password_hash}, first_name={self.first_name}, last_name={self.last_name})>"
