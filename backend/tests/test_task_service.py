from datetime import datetime

import pytest

from backend.models.task import Task, TaskStatus
from backend.models.time_entry import TimeEntry
from backend.models.user import User
from backend.services.task_service import (
    create_task,
    get_task_by_id,
    update_task,
    delete_task,
    get_tasks_without_time_entries,
    get_task_with_time_entries,
    update_total_duration_for_task,
)


@pytest.fixture()
def test_user(db_session):
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash="hashed_pw",
        first_name="Test",
        last_name="User",
    )
    db_session.add(user)
    db_session.commit()
    return user


def test_create_and_get_task(db_session, test_user):
    response = create_task(
        title="Test Task",
        description="This is a test",
        status="todo",
        user_id=test_user.user_id,
    )
    task = get_task_by_id(response["task_id"])
    assert task.title == "Test Task"
    assert task.status == TaskStatus.todo
    assert task.user_id == test_user.user_id


def test_update_task(db_session, test_user):
    task = Task(title="Old Title", user_id=test_user.user_id)
    db_session.add(task)
    db_session.commit()

    response = update_task(task.task_id, title="New Title", status="in_progress")
    updated_task = get_task_by_id(task.task_id)
    assert updated_task.title == "New Title"
    assert updated_task.status == TaskStatus.in_progress


def test_delete_task(db_session, test_user):
    task = Task(title="Delete Me", user_id=test_user.user_id)
    db_session.add(task)
    db_session.commit()

    response = delete_task(task.task_id)
    assert response["success"] is True
    assert get_task_by_id(task.task_id) is None


def test_get_tasks_without_time_entries(db_session, test_user):
    t1 = Task(title="No Entry", user_id=test_user.user_id)
    t2 = Task(title="With Entry", user_id=test_user.user_id)
    db_session.add_all([t1, t2])
    db_session.commit()

    entry = TimeEntry(
        task_id=t2.task_id,
        user_id=test_user.user_id,
        start_time=datetime.now(),
        end_time=datetime.now(),
        duration_seconds=600,
    )
    db_session.add(entry)
    db_session.commit()

    results = get_tasks_without_time_entries()
    assert t1 in results
    assert t2 not in results


def test_get_task_with_time_entries(db_session, test_user):
    task = Task(title="Tracked", user_id=test_user.user_id)
    db_session.add(task)
    db_session.commit()

    entry = TimeEntry(
        task_id=task.task_id,
        user_id=test_user.user_id,
        start_time=datetime.now(),
        end_time=datetime.now(),
        duration_seconds=1800,
    )
    db_session.add(entry)
    db_session.commit()

    result = get_task_with_time_entries(task.task_id)
    assert result["task"]["task_id"] == task.task_id
    assert len(result["time_entries"]) == 1
    assert result["time_entries"][0]["duration_seconds"] == 1800


def test_update_total_duration_for_task(db_session, test_user):
    task = Task(title="DurationTest", user_id=test_user.user_id)
    db_session.add(task)
    db_session.commit()

    entry1 = TimeEntry(
        task_id=task.task_id, user_id=test_user.user_id, duration_seconds=60
    )
    entry2 = TimeEntry(
        task_id=task.task_id, user_id=test_user.user_id, duration_seconds=120
    )
    db_session.add_all([entry1, entry2])
    db_session.commit()

    response = update_total_duration_for_task(task.task_id)
    assert response["total_duration_seconds"] == 180
    assert "03:00" in response["total_duration_formatted"]
