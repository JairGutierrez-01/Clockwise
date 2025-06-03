from datetime import datetime

from backend.models.notification import Notification


def test_notification_creation():
    notif = Notification(
        user_id=1,
        project_id=2,
        message="You were added to the project.",
        type="Uni",
        is_read=False,
        created_at=datetime.now(),
    )

    assert notif.user_id == 1
    assert notif.project_id == 2
    assert notif.message == "You were added to the project."
    assert notif.type == "Uni"
    assert notif.is_read is False
    assert isinstance(notif.created_at, datetime)
