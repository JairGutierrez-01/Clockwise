from datetime import datetime, timedelta

from backend.database import db


class TimeEntry(db.Model):
    """
    Represents a time tracking entry linked to a user for a specific task.

    Attributes:
        time_entry_id (int): Primary key.
        user_id (int): Foreign key referencing the user who created the entry.
        task_id (int): Foreign key referencing the related task.
        start_time (datetime): Timestamp when tracking started.
        end_time (datetime): Timestamp when tracking stopped.
        duration_seconds (int): Total duration in seconds.
        comment (str, optional): Optional comment.
        user (relationship): Related user object.
        task (relationship): Related task object.
    """

    __tablename__ = "time_entries"

    time_entry_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey("tasks.task_id"), nullable=False)
    start_time = db.Column(db.DateTime, nullable=True)
    end_time = db.Column(db.DateTime, nullable=True)
    duration_seconds = db.Column(db.Integer, nullable=True)
    comment = db.Column(db.String, nullable=True)

    user = db.relationship("User", back_populates="time_entries")
    task = db.relationship("Task", back_populates="time_entries")

    def __repr__(self):
        """
        Returns a short string representation of the TimeEntry instance for debugging purposes.
        """
        return f"<TimeEntry(id={self.time_entry_id}, user={self.user_id}, task={self.task_id})>"

    def to_dict(self):
        """
        Convert the time entry instance into a dictionary for JSON responses.

        Returns:
            dict: A dictionary representation of the time entry.
        """
        return {
            "time_entry_id": self.time_entry_id,
            "user_id": self.user_id,
            "task_id": self.task_id,
            "title": self.task.title,
            "project_name": (
                self.task.project.name if self.task and self.task.project else None
            ),
            "start_time": (
                self.start_time.strftime("%Y-%m-%d %H:%M:%S")
                if self.start_time
                else None
            ),
            "end_time": (
                self.end_time.strftime("%Y-%m-%d %H:%M:%S") if self.end_time else None
            ),
            "duration_seconds": self.duration_seconds,
            "duration": str(timedelta(seconds=self.duration_seconds or 0)),
            "comment": self.comment,
        }
