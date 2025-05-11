from sqlalchemy import Column, Integer, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base
from backend.database import db


class Project(db.Model):
    """
    Represents a project a user could be working on.

    Attributes:
        project_id (int): Identifier of the project, also primary key.
        name (str): The name of the project.
        description (str): The description of the project.
        team_id (int): Foreign key of the team the project belongs to.
        category_id (int): Foreign key identifying the category of the project.
        time_limit_hours (int): Limit of how much time the user wants to spend on the project.
        current_hours (int): How many hours the user already spent on the project.
        created_at (datetime): The timestamp when the project was created.
        due_date (datetime): Deadline for the project.
        type (enum): Project Type (TeamProject, SoloProject).
        is_course (bool): Statement if Project is a Course or not.
        credit_points (int, optional): The credit points of the course, if it is a course.
        task (relationship): The tasks the project contains.
        team (relationship): The team the project belongs to.
        user (relationship): The user the project belongs to.
        category (relationship): The category of the project.

    """

    __tablename__ = "projects"

    project_id = db.Column(db.Integer, primary_key=True, index=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=True)
    team_id = db.Column(db.Integer, db.ForeignKey("teams.team_id"), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.category_id"))
    time_limit_hours = db.Column(db.Integer, nullable=False)
    current_hours = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    due_date = db.Column(db.DateTime, nullable=True)
    type = db.Column(Enum(ProjectType), default=ProjectType.SoloProject, nullable=False)
    is_course = db.Column(db.Boolean)
    credit_points = db.Column(db.Integer, nullable=True)

    # Foreign Key to users.user_id
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"))

    task = db.relationship("Task", back_populates="project")
    team = db.relationship("Team", back_populates="project")
    user = db.relationship("User", back_populates="project")
    category = db.relationship("Category", back_populates="project")
    notifications = db.relationship("Notification", back_populates="project")

    def __repr__(self) -> str:
        """
        Returns a string representation of the project object.

        Returns:
            str: A string representation of the project object.
        """
        return f"<Project(id={self.project_id}, name={self.name}, team={self.team_id} category={self.category_id}, limit={self.time_limit_hours}, current={self.current_hours})>"
