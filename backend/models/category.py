from backend.database import db


class Category(db.Model):
    """
    Represents a task category in the system.

    Attributes:
        category_id (int): The unique identifier for the category (primary key).
        name (str): The name of the category.
        user_id (int): Foreign key linking to the user who owns this category.
        tasks (List[Task]): The list of tasks assigned to this category.
        user (User): The user who owns this category.
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
