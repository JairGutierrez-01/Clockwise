from datetime import datetime, timedelta

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
    """

    notification = Notification(
        user_id=user_id, message=message, type=notif_type, project_id=project_id
    )
    db.session.add(notification)
    db.session.commit()


# Used in: task_routes.py
# Trigger: A task is assigned to a user (F60)
def notify_task_assigned(user_id, task_name, project_name):
    """
    Notify user they were assigned a task.
    """
    message = (
        f"You were assigned the task '{task_name}' in the project '{project_name}'."
    )
    create_notification(user_id, message, notif_type="task")


# Used in: task_routes.py
# Trigger: Task was edited and reassigned to a new user (F60)
def notify_task_reassigned(user_id, task_name, project_name):
    """
    Notify user about task reassignment.
    """
    message = f"You are now responsible for the task '{task_name}' in the project '{project_name}'."
    create_notification(user_id, message, notif_type="task")


# Used in: task_routes.py
# Trigger: Task assignment removed (F60)
def notify_task_unassigned(user_id, task_name, project_name):
    """
    Notify user they were unassigned from a task.
    """
    message = f"You are no longer assigned to the task '{task_name}' in the project '{project_name}'."
    create_notification(user_id, message, notif_type="task")


# Used in: task_routes.py
# Trigger: Task was deleted from a team project
def notify_task_deleted(user_id, task_name, project_name):
    """
    Notify user their task was deleted.
    """
    message = f"Your task '{task_name}' in project '{project_name}' was deleted."
    create_notification(user_id, message, notif_type="task")


# Used in: user_team_routes.py
# Trigger: A user is added to a team (F100)
def notify_user_added_to_team(user_id, team_name):
    """
    Notify user they joined a team.
    """
    message = f"You were added to the team '{team_name}'."
    create_notification(user_id, message, notif_type="team")


# Used in: Soon analysis_routes.py
# Trigger: Progress deviates from weekly goal (F90 / RC6)
def notify_progress_deviation(user_id, project_name, deviation_percentage):
    """
    Notify user of project progress deviation.
    """
    message = f"Your progress in '{project_name}' deviates by {deviation_percentage}% from your weekly goal."
    create_notification(user_id, message, notif_type="progress")
    print(f"Abweichung erkannt: {project_name} weicht um {deviation_percentage}% ab.")


# Used in: project_routes.py
# Trigger: User creates a new project (F50)
def notify_project_created(user_id, project_name):
    """
    Notify user of project creation.
    """
    message = f"The project '{project_name}' was successfully created."
    create_notification(user_id, message, notif_type="project")


# Used in: analysis_service.py
# Trigger: Weekly goal reached (RC6)
def notify_weekly_goal_achieved(user_id, project_name):
    """
    Notify user that weekly goal was reached.
    """
    message = f"You reached your weekly goal for project '{project_name}'."
    create_notification(user_id, message, notif_type="progress")


def notify_task_overdue(user_id, task_name, due_date):
    """
    Notify user that weekly task are overdue.
    """
    msg = f"The task '{task_name}' is overdue since {due_date.strftime('%Y-%m-%d')}."
    create_notification(user_id, msg, notif_type="warning")


"""
def already_notified_this_week(user_id, project_name):
    one_week_ago = datetime.now() - timedelta(days=7)

    return (
        Notification.query.filter(
            Notification.user_id == user_id,
            Notification.type == "progress",
            Notification.message.ilike(f"%{project_name}%"),
            Notification.created_at >= one_week_ago,
        ).first()
        is not None
    )
"""


def already_notified_this_week(user_id, project_id, notif_type="progress"):
    now = datetime.now()
    start_of_week = now - timedelta(days=now.weekday())  # Montag 0 Uhr
    end_of_week = start_of_week + timedelta(days=7)

    exists = Notification.query.filter(
        Notification.user_id == user_id,
        Notification.project_id == project_id,
        Notification.type == notif_type,
        Notification.created_at >= start_of_week,
        Notification.created_at < end_of_week,
    ).first()
    return exists is not None
