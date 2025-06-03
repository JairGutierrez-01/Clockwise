from datetime import datetime, timedelta

from backend.database import db


class TimeEntry(db.Model):
    """
    Represents a time tracking entry made by a user for a specific task.
    Attributes:
        time_entry_id (int): Primary key.
        user_id (int): Foreign key to User.
        task_id (int): Foreign key to Task.
        start_time (datetime): When the time tracking started.
        end_time (datetime): When it ended.
        duration_seconds (int): Total duration in seconds.
        comment (str, optional): Optional note.
        user (relationship): The user who created the time entry.
        task (relationship): The task to which this time entry is assigned.
    """

    __tablename__ = "time_entries"

    time_entry_id = db.Column(db.Integer, primary_key=True, index=True)
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
        Returns a string representation of the TimeEntry instance.
        """
        return f"<TimeEntry(id={self.time_entry_id}, user={self.user_id}, task={self.task_id}, start={self.start_time}, end={self.end_time})>"

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
