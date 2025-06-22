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
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)

    tasks = db.relationship("Task", back_populates="category")
    user = db.relationship("User", back_populates="categories")

    def __repr__(self) -> str:
        """
        Returns a string representation of the category instance.

        Returns:
            str: A string representation of the category instance.
        """
        return f"<Category(id={self.category_id}, name={self.name})>"
