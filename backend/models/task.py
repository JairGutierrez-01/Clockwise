from sqlalchemy import Column, Integer, DateTime, ForeignKey, String, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base
import enum


class TaskStatus(enum.Enum):
    todo = "todo"
    in_progress = "in_progress"
    done = "done"

class Task(Base):
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
            time_entries (relationship):  All time entries associated with this task.
            assigned_user (relationship): The user currently assigned to this task.
            project (relationship): The project this task belongs to.
    """

    __tablename__ = "tasks"

    task_id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.project_id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=True)

    title = Column(String, nullable=True)
    description = Column(String, nullable=True)
    due_date = Column(DateTime, nullable=True)
    status = Column(Enum(TaskStatus), default=TaskStatus.todo, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    time_entries = relationship("TimeEntry", back_populates="task")
    assigned_user = relationship("User", back_populates="assigned_task")
    project = relationship("Project", back_populates="task")

    def __repr__(self):
        """
        Returns a string representation of the Task instance.
        """
        return f"<Task(id={self.task_id}, title={self.title}, project={self.project_id}, assigned_user={self.assigned_user_id}, status={self.status})>"