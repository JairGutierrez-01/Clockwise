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


# Used in: task_routes.py
# Trigger: A task is assigned to a user (F60)
def notify_task_assigned(user_id, task_name, project_name):
    message = (
        f"You were assigned the task '{task_name}' in the project '{project_name}'."
    )
    create_notification(user_id, message, notif_type="task")


# Used in: task_routes.py
# Trigger: Task was edited and reassigned to a new user (F60)
def notify_task_reassigned(user_id, task_name, project_name):
    message = f"You are now responsible for the task '{task_name}' in the project '{project_name}'."
    create_notification(user_id, message, notif_type="task")


# Used in: task_routes.py
# Trigger: Task assignment removed (F60)
def notify_task_unassigned(user_id, task_name, project_name):
    message = f"You are no longer assigned to the task '{task_name}' in the project '{project_name}'."
    create_notification(user_id, message, notif_type="task")


# Used in: user_team_routes.py
# Trigger: A user is added to a team (F100)
def notify_user_added_to_team(user_id, team_name):
    message = f"You were added to the team '{team_name}'."
    create_notification(user_id, message, notif_type="team")


# Used in: Soon analysis_routes.py
# Trigger: Progress deviates from weekly goal (F90 / RC6)
def notify_progress_deviation(user_id, project_name, deviation_percentage):
    message = f"Your progress in '{project_name}' deviates by {deviation_percentage}% from your weekly goal."
    create_notification(user_id, message, notif_type="progress")


# Used in: project_routes.py
# Trigger: User creates a new project (F50)
def notify_project_created(user_id, project_name):
    message = f"The project '{project_name}' was successfully created."
    create_notification(user_id, message, notif_type="project")


# Used in: analysis_service.py
# Trigger: Weekly goal reached (RC6)
def notify_weekly_goal_achieved(user_id, project_name):
    message = f"You reached your weekly goal for project! '{project_name}'."
    create_notification(user_id, message, notif_type="progress")
