from backend.database import db
from backend.models.notification import Notification


def create_notification(user_id, message, notif_type="info", project_id=None):
    """
    Creates a new notification for a specific user.

    Args:
        user_id (int): ID of the user who should receive the notification.
        message (str): Text content of the notification.
        notif_type (str): Type/category of the notification (e.g. "team", "task", "info").
        project_id (int, optional): Related project ID, if applicable.

    if you want to use this function in a route, you need to add the following:
    from backend.services.notifications import create_notification

    the function will be called like this:
    create_notification(user_id, message, notif_type="info", project_id=None)

    an example of a notification could look like this:
    create_notification(user_id=1, message="You were added to the team!.", notif_type="team", project_id=1)
    """

    notification = Notification(
        user_id=user_id, message=message, type=notif_type, project_id=project_id
    )
    db.session.add(notification)
    db.session.commit()
