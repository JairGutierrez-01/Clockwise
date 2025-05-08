from datetime import datetime
from backend.database import Base

# TODO: Define the Notification model (SQLAlchemy)

# - Attributes:
#     - id: primary key
#     - user_id: foreign key to User (required)
#     - project_id: foreign key to Project (optional)
#     - message: string/text
#     - created_at: datetime, auto-set
#     - type: string (e.g. "info", "warning", "limit_reached")

# - Relationships:
#     - user: backref to User
#     - project: backref to Project

# TODO: Plan logic for automatic notifications (z.B. time limit exceeded)
# TODO: Add API routes:
#     - Get all notifications for a user
#     - Mark notification as read
#     - Delete notification