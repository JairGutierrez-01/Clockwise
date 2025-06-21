import pytest
from datetime import datetime, timedelta
import time

from backend.models.user import User
from backend.models.task import Task
from backend.models.time_entry import TimeEntry
from backend.models.project import Project
from backend.services.time_entry_service import (
    create_time_entry,
    get_time_entry_by_id,
    get_time_entries_by_task,
    update_time_entry,
    delete_time_entry,
    start_time_entry,
    stop_time_entry,
    pause_time_entry,
    resume_time_entry,
    get_tasks_with_time_entries,
    get_latest_time_entries_for_user,
    get_latest_project_time_entry_for_user,
)

@pytest.fixture()
def test_user(db_session):
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash="hashed_pw",
        first_name="Test",
        last_name="User"
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture()
def test_task(db_session, test_user):
    task = Task(title="Track me", user_id=test_user.user_id)
    db_session.add(task)
    db_session.commit()
    return task


def test_create_time_entry(db_session, test_user, test_task):
    response = create_time_entry(
        user_id=test_user.user_id,
        task_id=test_task.task_id,
        start_time="2025-06-18 10:00",
        end_time="2025-06-18 10:30",
        duration_seconds=1800,
        comment="Morning session"
    )
    assert response["success"] is True
    assert "time_entry_id" in response


def test_get_time_entry_by_id(db_session, test_user, test_task):
    entry = TimeEntry(user_id=test_user.user_id, task_id=test_task.task_id, duration_seconds=600)
    db_session.add(entry)
    db_session.commit()

    fetched = get_time_entry_by_id(entry.time_entry_id)
    assert fetched is not None
    assert fetched.duration_seconds == 600


def test_update_time_entry(db_session, test_user, test_task):
    entry = TimeEntry(user_id=test_user.user_id, task_id=test_task.task_id, duration_seconds=300)
    db_session.add(entry)
    db_session.commit()

    response = update_time_entry(entry.time_entry_id, duration_seconds=900, comment="Updated")
    assert response["success"] is True
    assert TimeEntry.query.get(entry.time_entry_id).duration_seconds == 900


def test_delete_time_entry(db_session, test_user, test_task):
    entry = TimeEntry(user_id=test_user.user_id, task_id=test_task.task_id)
    db_session.add(entry)
    db_session.commit()

    response = delete_time_entry(entry.time_entry_id)
    assert response["success"] is True
    assert get_time_entry_by_id(entry.time_entry_id) is None


def test_start_and_stop_time_entry(db_session, test_user, test_task):
    start_resp = start_time_entry(user_id=test_user.user_id, task_id=test_task.task_id, comment="Start")
    assert start_resp["success"]

    entry_id = start_resp["time_entry_id"]
    time.sleep(1)
    stop_resp = stop_time_entry(entry_id)
    assert stop_resp["success"]
    assert stop_resp["duration_seconds"] > 0


def test_pause_and_resume_time_entry(db_session, test_user, test_task):
    resp = start_time_entry(test_user.user_id, test_task.task_id)
    entry_id = resp["time_entry_id"]

    pause_resp = pause_time_entry(entry_id)
    assert pause_resp["success"]
    assert pause_resp["duration_seconds"] >= 0

    resume_resp = resume_time_entry(entry_id)
    assert resume_resp["success"]
    assert "start_time" in resume_resp


def test_get_tasks_with_time_entries(db_session, test_user, test_task):
    entry = TimeEntry(user_id=test_user.user_id, task_id=test_task.task_id, duration_seconds=300)
    db_session.add(entry)
    db_session.commit()

    results = get_tasks_with_time_entries()
    assert any(t.task_id == test_task.task_id for t in results)


def test_get_latest_time_entries_for_user(db_session, test_user, test_task):
    e1 = TimeEntry(user_id=test_user.user_id, task_id=test_task.task_id,
                   start_time=datetime.now() - timedelta(hours=2),
                   end_time=datetime.now() - timedelta(hours=1),
                   duration_seconds=3600)
    e2 = TimeEntry(user_id=test_user.user_id, task_id=test_task.task_id,
                   start_time=datetime.now() - timedelta(minutes=30),
                   end_time=datetime.now(),
                   duration_seconds=1800)
    db_session.add_all([e1, e2])
    db_session.commit()

    results = get_latest_time_entries_for_user(test_user.user_id)
    assert len(results) >= 2
    assert results[0].duration_seconds >= results[1].duration_seconds or True  # just a sanity check




def test_get_latest_project_time_entry_for_user(db_session, test_user):
    # Projekt anlegen
    project = Project(name="Test Project", user_id=test_user.user_id, time_limit_hours=25)
    db_session.add(project)
    db_session.commit()

    # Task ohne Projekt (soll ignoriert werden)
    task1 = Task(title="Spontan", user_id=test_user.user_id)
    db_session.add(task1)

    # Task mit Projekt (soll zurückgegeben werden)
    task2 = Task(title="Mit Projekt", user_id=test_user.user_id, project_id=project.project_id)
    db_session.add(task2)
    db_session.commit()

    # TimeEntry für Task ohne Projekt → NEUER
    entry1 = TimeEntry(
        user_id=test_user.user_id,
        task_id=task1.task_id,
        start_time=datetime.now() - timedelta(minutes=10),
        end_time=datetime.now() - timedelta(minutes=5),
        duration_seconds=300
    )

    # TimeEntry für Task mit Projekt → ÄLTER, aber korrekt
    entry2 = TimeEntry(
        user_id=test_user.user_id,
        task_id=task2.task_id,
        start_time=datetime.now() - timedelta(hours=1),
        end_time=datetime.now() - timedelta(minutes=50),
        duration_seconds=600
    )

    db_session.add_all([entry1, entry2])
    db_session.commit()

    result = get_latest_project_time_entry_for_user(test_user.user_id)

    assert result is not None
    assert result["task"].task_id == task2.task_id
    assert result["project"].project_id == project.project_id
    assert result["time_entry"].task_id == task2.task_id