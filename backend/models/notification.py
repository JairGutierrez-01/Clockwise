from datetime import datetime

from backend.database import db


class Notification(db.Model):
    """
    Database model for user notifications related to projects or system events.

    Attributes:
        id (int): Identifier of the Notification, also primary key.
        user_id (int): Foreign key of the user the Notification belongs to.
        project_id (int): Foreign key of the project the Notification belongs to.
        message (str): The message of the Notification.
        created_at (datetime): The timestamp when the Notification was created.
        type (str): The type of the Notification.
        is_read (bool): Statement if Notification is read or not.
        user (relationship): The user the Notification belongs to.
        project (relationship): The project the Notification belongs to.

    """

    __tablename__ = "notifications"

    #   Attributes
    id = db.Column(db.Integer, primary_key=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    project_id = db.Column(
        db.Integer, db.ForeignKey("projects.project_id"), nullable=True
    )
    message = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    type = db.Column(db.String, nullable=False)
    is_read = db.Column(db.Boolean, default=False)

    #   Relationships
    user = db.relationship("User", back_populates="notifications")
    project = db.relationship("Project", back_populates="notifications")
