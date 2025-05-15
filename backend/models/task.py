from sqlalchemy import Column, Integer, DateTime, ForeignKey, String, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base, db
import enum


class TaskStatus(enum.Enum):
    """Enumeration of possible task statuses."""
    todo = "todo"
    in_progress = "in_progress"
    done = "done"


class Task(db.Model):
    """
    Represents a task that belongs to a project and may be assigned to a user.

    Attributes:
        task_id (int): Primary key of the task.
        project_id (int): Foreign key linking the task to a project.
        user_id (int): Foreign key linking the task to the assigned user.
        category_id (int): Foreign key linking the task to a category.
        title (str, optional): Short title of the task.
        description (str, optional): Detailed description of the task.
        due_date (datetime, optional): Deadline for the task.
        status (enum): Task status (todo, in_progress, done).
        created_at (datetime): Timestamp when the task was created.
        category_id (int): Foreign key identifying the category of the tasks.
        time_entries (relationship):  All time entries associated with this task.
        assigned_user (relationship): The user currently assigned to this task.
        project (relationship): The project this task belongs to.
        category (relationship): The category this task belongs to.
    """

    __tablename__ = "tasks"

    task_id = db.Column(db.Integer, primary_key=True, index=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.project_id"), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.category_id"), nullable=True)
    title = db.Column(db.String, nullable=True)
    description = db.Column(db.String, nullable=True)
    due_date = db.Column(db.DateTime, nullable=True)
    status = db.Column(Enum(TaskStatus), default=TaskStatus.todo, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)

    time_entries = db.relationship("TimeEntry", back_populates="task", uselist=False)
    assigned_user = db.relationship("User", back_populates="assigned_task")
    project = db.relationship("Project", back_populates="task")
    category = db.relationship("Category", back_populates="task")

    def __repr__(self):
        """
        Returns a string representation of the Task instance.
        """
        project_part = self.project_id if self.project_id else "Default"
        category_name = self.category.name if self.category else "None"
        return (
            f"<Task(id={self.task_id}, title={self.title}, project={project_part}, "
            f"user_id={self.user_id}, category={category_name}, status={self.status})>"
        )