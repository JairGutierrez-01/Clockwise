from sqlalchemy import Column, Integer, DateTime, ForeignKey, String, Enum
from sqlalchemy.orm import relationship
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from backend.database import Base
from backend.database import db
import enum


class ProjectType(enum.Enum):
    TeamProject = "TeamProject"
    SoloProject = "SoloProject"


class Project(db.Model):
    """
    Represents a project a user could be working on.

    Attributes:
        project_id (int): Identifier of the project, also primary key.
        name (str): The name of the project.
        description (str): The description of the project.
        time_limit_hours (int): Limit of how much time the user wants to spend on the project.
        current_hours (int): How many hours the user already spent on the project.
        created_at (datetime): The timestamp when the project was created.
        due_date (datetime): Deadline for the project.
        type (enum): Project Type (TeamProject, SoloProject).
        is_course (bool): Statement if Project is a Course or not.
        credit_points (int, optional): The credit points of the course, if it is a course.
        user_id (int): Foreign key of the user the project belongs to.
        team_id (int): Foreign key of the team the project belongs to.
        task (relationship): The tasks the project contains.
        team (relationship): The team the project belongs to.
        user (relationship): The user the project belongs to.
        notification (relationship): The notification of the project.
    """

    __tablename__ = "projects"

    project_id = db.Column(db.Integer, primary_key=True, index=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=True)
    time_limit_hours = db.Column(db.Integer, nullable=False)
    current_hours = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    due_date = db.Column(db.DateTime, nullable=True)
    type = db.Column(Enum(ProjectType), default=ProjectType.SoloProject, nullable=False)
    is_course = db.Column(db.Boolean)
    credit_points = db.Column(db.Integer, nullable=True)

    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey("teams.team_id"), nullable=True)

    tasks = db.relationship("Task", back_populates="project", cascade="all, delete-orphan")
    team = db.relationship("Team", back_populates="project")
    user = db.relationship("User", back_populates="project")
    notifications = db.relationship("Notification", back_populates="project")

    def __repr__(self) -> str:
        """
        Returns a string representation of the project object.

        Returns:
            str: A string representation of the project object.
        """
        return f"<Project(id={self.project_id}, name={self.name}, team={self.team_id} category={self.category_id}, limit={self.time_limit_hours}, current={self.current_hours})>"
