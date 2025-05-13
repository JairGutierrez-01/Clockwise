from sqlalchemy import Column, Integer, DateTime, ForeignKey, String, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base, db
import enum


class TaskStatus(enum.Enum):
    todo = "todo"
    in_progress = "in_progress"
    done = "done"


class Task(db.Model):
    """
    Represents a task that belongs to a project and may be assigned to a user.

    Attributes:
        task_id (int): Primary key of the task.
        project_id (int): Foreign key linking the task to a project.
        assigned_user_id (int, optional): Foreign key to the assigned user.
        title (str, optional): Short title of the task.
        description (str, optional): Detailed description of the task.
        due_date (datetime, optional): Deadline for the task.
        status (enum): Task status (todo, in_progress, done).
        created_at (datetime): Timestamp when the task was created.
        category_id (int): Foreign key identifying the category of the tasks.
        time_entries (relationship):  All time entries associated with this task.
        assigned_user (relationship): The user currently assigned to this task.
        project (relationship): The project this task belongs to.
        category (relationship): The category of the task.
    """

    __tablename__ = "tasks"

    task_id = db.Column(db.Integer, primary_key=True, index=True)
    project_id = db.Column(
        db.Integer, db.ForeignKey("projects.project_id"), nullable=False
    )
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True)
    title = db.Column(db.String, nullable=True)
    description = db.Column(db.String, nullable=True)
    due_date = db.Column(db.DateTime, nullable=True)
    status = db.Column(Enum(TaskStatus), default=TaskStatus.todo, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.category_id"))

    time_entries = db.relationship("TimeEntry", back_populates="task")
    assigned_user = db.relationship("User", back_populates="assigned_task")
    project = db.relationship("Project", back_populates="task")
    category = db.relationship("Category", back_populates="task")

    def __repr__(self):
        """
        Returns a string representation of the Task instance.
        """
        return f"<Task(id={self.task_id}, title={self.title}, project={self.project_id}, assigned_user={self.assigned_user_id}, status={self.status})>"
