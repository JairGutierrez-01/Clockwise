"""Model package initializer.

This module imports and exposes all database models used in the application.

Modules:
    user (User): Contains the User model.
    user_team (UserTeam): Contains the UserTeam model.
    team (Team): Contains the Team model.
    project (Project): Contains the Project model.
    task (Task): Contains the Task model.
    time_entry (TimeEntry): Contains the TimeEntry model.
    notification (Notification): Contains the Notification model.
    category (Category): Contains the Category model.

Exports:
    User: The User model class.
    UserTeam: The UserTeam association model class.
    Team: The Team model class.
    Project: The Project model class.
    Task: The Task model class.
    TimeEntry: The TimeEntry model class.
    Notification: The Notification model class.
    Category: The Category model class.
"""

from backend.models.user import User
from backend.models.user_team import UserTeam
from backend.models.team import Team
from backend.models.project import Project
from backend.models.task import Task
from backend.models.time_entry import TimeEntry
from backend.models.notification import Notification
from backend.models.category import Category

__all__ = [
    "User",
    "UserTeam",
    "Team",
    "Project",
    "Task",
    "TimeEntry",
    "Notification",
    "Category",
]
