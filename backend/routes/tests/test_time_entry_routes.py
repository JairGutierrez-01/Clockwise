import json
from datetime import datetime, timedelta
import pytest

from backend.models.user import User
from backend.models.task import Task
from backend.models.time_entry import TimeEntry
from backend.models.project import Project
from backend.services.time_entry_service import get_latest_project_time_entry_for_user



@pytest.fixture()
def test_user(db_session):
    user = User(
        username="entryapi",
        email="entry@example.com",
        password_hash="pw",
        first_name="Entry",
        last_name="User",
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture()
def test_task(db_session, test_user):
    task = Task(title="APITask", user_id=test_user.user_id)
    db_session.add(task)
    db_session.commit()
    return task


def login_test_user(client, test_user):
    with client.session_transaction() as session:
        session["_user_id"] = str(test_user.user_id)


def test_create_time_entry_api(client, db_session, test_user, test_task):
    login_test_user(client, test_user)
    payload = {
        "task_id": test_task.task_id,
        "start_time": "2025-06-18 10:00",
        "end_time": "2025-06-18 10:30",
        "duration_seconds": 1800,
        "comment": "Morning"
    }
    response = client.post("/api/time_entries/", data=json.dumps(payload), content_type="application/json")
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"]
    assert "time_entry_id" in data


def test_get_time_entry_by_id_api(client, db_session, test_user, test_task):
    login_test_user(client, test_user)
    entry = TimeEntry(user_id=test_user.user_id, task_id=test_task.task_id, duration_seconds=600)
    db_session.add(entry)
    db_session.commit()

    response = client.get(f"/api/time_entries/{entry.time_entry_id}")
    assert response.status_code == 200
    data = response.get_json()
    assert data["duration_seconds"] == 600


def test_update_time_entry_api(client, db_session, test_user, test_task):
    login_test_user(client, test_user)
    entry = TimeEntry(user_id=test_user.user_id, task_id=test_task.task_id, duration_seconds=300)
    db_session.add(entry)
    db_session.commit()

    payload = {"duration_seconds": 900, "comment": "Updated via API"}
    response = client.put(f"/api/time_entries/{entry.time_entry_id}", data=json.dumps(payload), content_type="application/json")
    assert response.status_code == 200
    assert response.get_json()["success"]


def test_delete_time_entry_api(client, db_session, test_user, test_task):
    login_test_user(client, test_user)
    entry = TimeEntry(user_id=test_user.user_id, task_id=test_task.task_id)
    db_session.add(entry)
    db_session.commit()

    response = client.delete(f"/api/time_entries/{entry.time_entry_id}")
    assert response.status_code == 200
    assert response.get_json()["success"]


def test_get_tasks_without_entries_api(client, db_session, test_user):
    login_test_user(client, test_user)
    task = Task(title="No Entry", user_id=test_user.user_id)
    db_session.add(task)
    db_session.commit()

    response = client.get("/api/time_entries/available-tasks")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert any(t["title"] == "No Entry" for t in data)


def test_start_and_stop_entry_api(client, db_session, test_user, test_task):
    login_test_user(client, test_user)

    # Start entry
    payload = {"task_id": test_task.task_id, "comment": "Test start"}
    start_response = client.post("/api/time_entries/start", data=json.dumps(payload), content_type="application/json")
    assert start_response.status_code == 200
    start_data = start_response.get_json()
    assert start_data["success"]

    # Stop entry
    entry_id = start_data["time_entry_id"]
    stop_response = client.post(f"/api/time_entries/stop/{entry_id}")
    assert stop_response.status_code == 200
    assert stop_response.get_json()["success"]


def test_get_latest_project_time_entry_for_user(db_session, test_user):
    # Projekt und zwei Tasks
    project = Project(name="Testprojekt", user_id=test_user.user_id, time_limit_hours=25)
    db_session.add(project)
    db_session.commit()

    task1 = Task(title="Mit Projekt", user_id=test_user.user_id, project_id=project.project_id)
    task2 = Task(title="Ohne Projekt", user_id=test_user.user_id)
    db_session.add_all([task1, task2])
    db_session.commit()

    # Neuerer Entry ohne Projekt
    entry1 = TimeEntry(
        user_id=test_user.user_id,
        task_id=task2.task_id,
        start_time=datetime.now() - timedelta(minutes=20),
        end_time=datetime.now() - timedelta(minutes=10),
        duration_seconds=600
    )

    # Älterer Entry mit Projekt
    entry2 = TimeEntry(
        user_id=test_user.user_id,
        task_id=task1.task_id,
        start_time=datetime.now() - timedelta(hours=2),
        end_time=datetime.now() - timedelta(hours=1, minutes=30),
        duration_seconds=1800
    )

    db_session.add_all([entry1, entry2])
    db_session.commit()

    result = get_latest_project_time_entry_for_user(test_user.user_id)

    assert result is not None
    assert result["time_entry"].time_entry_id == entry2.time_entry_id
    assert result["task"].task_id == task1.task_id
    assert result["project"].project_id == project.project_id
