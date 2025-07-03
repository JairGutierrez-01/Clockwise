from datetime import datetime
import pytest

from backend.models.task import Task, TaskStatus
from backend.models.time_entry import TimeEntry
from backend.models.user import User
from backend.models.project import Project
from backend.services.task_service import (
    create_task,
    get_task_by_id,
    update_task,
    delete_task,
    get_tasks_without_time_entries,
    update_total_duration_for_task,
    get_unassigned_tasks,
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


@pytest.fixture()
def test_project(db_session, test_user):
    project = Project(
        name="Test Project",
        type="SoloProject",
        status="active",
        time_limit_hours=10,
        user_id=test_user.user_id,
    )
    db_session.add(project)
    db_session.commit()
    return project


def test_create_task_solo(db_session, test_user, test_project, monkeypatch):
    monkeypatch.setattr("backend.services.task_service.current_user", test_user)

    response = create_task(
        title="Test Task",
        description="A solo project task",
        project_id=test_project.project_id,
        status="todo",
    )
    task = get_task_by_id(response["task_id"])
    assert task.title == "Test Task"
    assert task.status == TaskStatus.todo
    assert task.project_id == test_project.project_id
    assert task.user_id == test_user.user_id


def test_create_task_default(db_session, test_user, monkeypatch):
    monkeypatch.setattr("backend.services.task_service.current_user", test_user)

    response = create_task(
        title="Default Task",
        description="A default task without project",
    )
    task = get_task_by_id(response["task_id"])
    assert task.title == "Default Task"
    assert task.project_id is None
    assert task.user_id == test_user.user_id


def test_update_task(db_session, test_user, monkeypatch):
    monkeypatch.setattr("backend.services.task_service.current_user", test_user)

    task = Task(title="Old Title", user_id=test_user.user_id)
    db_session.add(task)
    db_session.commit()

    update_task(task.task_id, title="New Title", status="in_progress")
    updated = get_task_by_id(task.task_id)
    assert updated.title == "New Title"
    assert updated.status == TaskStatus.in_progress


def test_delete_task(db_session, test_user, monkeypatch):
    monkeypatch.setattr("backend.services.task_service.current_user", test_user)

    task = Task(title="ToDelete", user_id=test_user.user_id)
    db_session.add(task)
    db_session.commit()

    delete_task(task.task_id)
    assert get_task_by_id(task.task_id) is None


def test_get_tasks_without_time_entries(db_session, test_user, monkeypatch):
    monkeypatch.setattr("backend.services.task_service.current_user", test_user)

    t1 = Task(title="No Entry", user_id=test_user.user_id)
    t2 = Task(title="With Entry", user_id=test_user.user_id)
    db_session.add_all([t1, t2])
    db_session.commit()

    entry = TimeEntry(
        task_id=t2.task_id,
        user_id=test_user.user_id,
        start_time=datetime.now(),
        end_time=datetime.now(),
        duration_seconds=120,
    )
    db_session.add(entry)
    db_session.commit()

    results = get_tasks_without_time_entries(test_user.user_id)
    assert t1 in results
    assert t2 not in results


def test_update_total_duration_for_task(db_session, test_user, monkeypatch):
    monkeypatch.setattr("backend.services.task_service.current_user", test_user)

    task = Task(title="Duration", user_id=test_user.user_id)
    db_session.add(task)
    db_session.commit()

    db_session.add_all([
        TimeEntry(task_id=task.task_id, user_id=test_user.user_id, duration_seconds=100),
        TimeEntry(task_id=task.task_id, user_id=test_user.user_id, duration_seconds=200),
    ])
    db_session.commit()

    result = update_total_duration_for_task(task.task_id)
    assert result["total_duration_seconds"] == 300
    assert result["total_duration_formatted"].startswith("0:05:00")


def test_get_unassigned_tasks(db_session, test_user):
    # ein Task ohne Projekt → unassigned
    unassigned_task = Task(
        title="I am unassigned",
        user_id=test_user.user_id,
        project_id=None,
    )
    db_session.add(unassigned_task)

    # Task mit gültigem Projekt → darf nicht erscheinen
    project = Project(
        name="Another Project",
        type="SoloProject",
        status="active",
        time_limit_hours=5,
        user_id=test_user.user_id,
    )
    db_session.add(project)
    db_session.commit()

    project_task = Task(
        title="With project",
        user_id=test_user.user_id,
        project_id=project.project_id,
    )
    db_session.add(project_task)

    db_session.commit()

    results = get_unassigned_tasks(test_user.user_id)

    assert unassigned_task in results
    assert project_task not in results
