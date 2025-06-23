import pytest

from backend.models import Notification, User
from backend.services.notifications import (
    create_notification,
    notify_task_assigned,
    notify_task_reassigned,
    notify_task_unassigned,
    notify_task_deleted,
    notify_user_added_to_team,
    notify_progress_deviation,
    notify_project_created,
    notify_weekly_goal_achieved,
)


@pytest.fixture
def setup_notify_user(db_session):
    user = User(username="notifyme", email="notify@example.com", password_hash="123")
    db_session.add(user)
    db_session.commit()
    return user


def test_create_notification_basic(db_session, setup_notify_user):
    user = setup_notify_user
    create_notification(user.user_id, "Test message", "info", project_id=123)

    note = Notification.query.filter_by(user_id=user.user_id).first()
    assert note is not None
    assert note.message == "Test message"
    assert note.type == "info"
    assert note.project_id == 123


def test_notify_task_assigned(db_session, setup_notify_user):
    user = setup_notify_user
    notify_task_assigned(user.user_id, "Task A", "Project X")

    note = Notification.query.filter_by(user_id=user.user_id).first()
    assert "assigned the task 'Task A'" in note.message
    assert note.type == "task"


def test_notify_task_reassigned(db_session, setup_notify_user):
    user = setup_notify_user
    notify_task_reassigned(user.user_id, "Task B", "Project Y")

    note = Notification.query.filter_by(user_id=user.user_id).first()
    assert "now responsible for the task 'Task B'" in note.message
    assert note.type == "task"


def test_notify_task_unassigned(db_session, setup_notify_user):
    user = setup_notify_user
    notify_task_unassigned(user.user_id, "Task C", "Project Z")

    note = Notification.query.filter_by(user_id=user.user_id).first()
    assert "no longer assigned to the task 'Task C'" in note.message
    assert note.type == "task"


def test_notify_task_deleted(db_session, setup_notify_user):
    user = setup_notify_user
    notify_task_deleted(user.user_id, "Task D", "Project W")

    note = Notification.query.filter_by(user_id=user.user_id).first()
    assert "Your task 'Task D'" in note.message
    assert note.type == "task"


def test_notify_user_added_to_team(db_session, setup_notify_user):
    user = setup_notify_user
    notify_user_added_to_team(user.user_id, "DevTeam")

    note = Notification.query.filter_by(user_id=user.user_id).first()
    assert "added to the team 'DevTeam'" in note.message
    assert note.type == "team"


def test_notify_progress_deviation(db_session, setup_notify_user):
    user = setup_notify_user
    notify_progress_deviation(user.user_id, "AnalyticsProject", deviation_percentage=15)

    note = Notification.query.filter_by(user_id=user.user_id).first()
    assert "deviates by 15%" in note.message
    assert note.type == "progress"


def test_notify_project_created(db_session, setup_notify_user):
    user = setup_notify_user
    notify_project_created(user.user_id, "MyNewProj")

    note = Notification.query.filter_by(user_id=user.user_id).first()
    assert "project 'MyNewProj' was successfully created" in note.message
    assert note.type == "project"


def test_notify_weekly_goal_achieved(db_session, setup_notify_user):
    user = setup_notify_user
    notify_weekly_goal_achieved(user.user_id, "GoalProject")

    note = Notification.query.filter_by(user_id=user.user_id).first()
    assert "reached your weekly goal" in note.message
    assert note.type == "progress"
