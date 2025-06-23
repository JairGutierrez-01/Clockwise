from datetime import datetime

import pytest

from backend.models.task import Task
from backend.models.time_entry import TimeEntry
from backend.models.user import User


@pytest.fixture()
def test_user(db_session):
    """Fixture für einen einmalig erstellten Test-User."""
    user = User(
        username="timetracker",
        email="t@example.com",
        password_hash="pw",
        first_name="T",
        last_name="T",
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture()
def test_task(db_session, test_user):
    """Fixture für eine einmalig erstellte Test-Task, die dem Test-User gehört."""
    task = Task(title="Timed Task", user_id=test_user.user_id)
    db_session.add(task)
    db_session.commit()
    return task


def test_create_time_entry(db_session, test_user, test_task):
    """Testet das Erstellen eines TimeEntry und die Verknüpfung zu User und Task."""
    entry = TimeEntry(
        user_id=test_user.user_id,
        task_id=test_task.task_id,
        start_time=datetime(2025, 6, 18, 10, 0),
        end_time=datetime(2025, 6, 18, 11, 0),
        duration_seconds=3600,
        comment="Worked on task",
    )
    db_session.add(entry)
    db_session.commit()

    fetched = db_session.query(TimeEntry).first()
    assert fetched is not None
    assert fetched.user_id == test_user.user_id
    assert fetched.task_id == test_task.task_id
    assert fetched.duration_seconds == 3600
    assert fetched.comment == "Worked on task"


def test_time_entry_repr(db_session, test_user, test_task):
    """Testet die __repr__-Ausgabe eines TimeEntry."""
    entry = TimeEntry(user_id=test_user.user_id, task_id=test_task.task_id)
    db_session.add(entry)
    db_session.commit()

    result = repr(entry)
    assert "<TimeEntry" in result
    assert f"user={test_user.user_id}" in result


def test_time_entry_to_dict(db_session, test_user, test_task):
    """Testet die to_dict()-Konvertierung eines TimeEntry."""
    entry = TimeEntry(
        user_id=test_user.user_id,
        task_id=test_task.task_id,
        start_time=datetime(2025, 6, 18, 9, 0),
        end_time=datetime(2025, 6, 18, 10, 30),
        duration_seconds=5400,
        comment="Session",
    )
    db_session.add(entry)
    db_session.commit()

    result = entry.to_dict()
    assert result["user_id"] == test_user.user_id
    assert result["task_id"] == test_task.task_id
    assert result["duration_seconds"] == 5400
    assert "duration" in result
    assert result["comment"] == "Session"
    assert result["title"] == test_task.title
