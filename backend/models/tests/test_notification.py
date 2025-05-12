from backend.models.team import Team
from backend.models.project import Project
from backend.models.user import User
from backend.models.notification import Notification
from backend.models.user_team import UserTeam
from backend.models.task import Task
from backend.models.time_entry import TimeEntry
from backend.models.category import Category
from datetime import datetime


def test_notification_creation():
    notif = Notification(
        user_id=1,
        project_id=2,
        message="You were added to the project.",
        type="Uni",
        is_read=False,
        created_at=datetime.now()
    )

    assert notif.user_id == 1
    assert notif.project_id == 2
    assert notif.message == "You were added to the project."
    assert notif.type == "Uni"
    assert notif.is_read is False
    assert isinstance(notif.created_at, datetime)