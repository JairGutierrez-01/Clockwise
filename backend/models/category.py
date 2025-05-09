from sqlalchemy import Column, Integer, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base
from backend.database import db


class Category(db.Model):
    """
    Represents the categories the projects could have.

    Attributes:
        category_id (int): Primary key identifying the category.
        name (str): The name of the category.
        project (relationship): Defines the category of a project.

    """

    __tablename__ = "categories"

    category_id = db.Column(db.Integer, primary_key=True, index=True)
    name = db.Column(db.String, nullable=False)

    project = db.relationship("Project", back_populates="category")

    def __repr__(self) -> str:
        """
        Returns a string representation of the category instance.

        Returns:
            str: A string representation of the category instance.
        """
        return f"<Project(id={self.category_id}, name={self.name})>"
