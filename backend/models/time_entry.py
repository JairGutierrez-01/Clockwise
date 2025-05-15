from sqlalchemy import Column, Integer, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base, db


class TimeEntry(db.Model):
    """
    Represents a time tracking entry made by a user for a specific task.
    Attributes:
        time_entry_id (int): Primary key.
        user_id (int): Foreign key to User.
        task_id (int): Foreign key to Task.
        start_time (datetime): When the time tracking started.
        end_time (datetime): When it ended.
        duration_minutes (int): Total duration in minutes.
        comment (str, optional): Optional note.
        user (relationship): The user who created the time entry.
        task (relationship): The task to which this time entry is assigned.
    """

    __tablename__ = "time_entries"

    time_entry_id = db.Column(db.Integer, primary_key=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey("tasks.task_id"), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.now)
    end_time = db.Column(db.DateTime, nullable=True)
    duration_minutes = db.Column(db.Integer, nullable=True)
    comment = db.Column(db.String, nullable=True)

    user = db.relationship("User", back_populates="time_entries")
    task = db.relationship("Task", back_populates="time_entries")

    def __repr__(self):
        """
        Returns a string representation of the TimeEntry instance.
        """
        return f"<TimeEntry(id={self.time_entry_id}, user={self.user_id}, task={self.task_id}, start={self.start_time}, end={self.end_time})>"
