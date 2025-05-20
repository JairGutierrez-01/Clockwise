from sqlalchemy import Column, Integer, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from backend.database import Base
from backend.database import db


class Category(db.Model):
    """
    Represents the categories the tasks could have.

    Attributes:
        category_id (int): Primary key identifying the category.
        name (str): The name of the category.
        task (relationship): Defines the category of a task.
    """

    __tablename__ = "categories"

    category_id = db.Column(db.Integer, primary_key=True, index=True)
    name = db.Column(db.String, nullable=False)

    task = db.relationship("Task", back_populates="category")

    def __repr__(self) -> str:
        """
        Returns a string representation of the category instance.

        Returns:
            str: A string representation of the category instance.
        """
        return f"<Category(id={self.category_id}, name={self.name})>"
