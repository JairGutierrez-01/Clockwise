import json
from datetime import datetime
import pytest

from backend.models.user import User
from backend.models.task import Task


@pytest.fixture()
def test_user(db_session):
    user = User(
        username="apiuser",
        email="api@example.com",
        password_hash="pw",
        first_name="API",
        last_name="User",
    )
    db_session.add(user)
    db_session.commit()
    return user


def login_test_user(client, test_user):
    with client.session_transaction() as session:
        session["_user_id"] = str(test_user.user_id)


def test_create_task_api(client, db_session, test_user):
    login_test_user(client, test_user)
    payload = {
        "title": "New Task",
        "description": "Via API",
        "due_date": "2025-12-31",
        "category_id": None,
        "project_id": None
    }
    response = client.post("/api/tasks", data=json.dumps(payload), content_type="application/json")
    assert response.status_code == 201
    data = response.get_json()
    assert data["success"]
    assert "task_id" in data


def test_get_task_by_id_api(client, db_session, test_user):
    login_test_user(client, test_user)
    task = Task(title="Fetch Me", user_id=test_user.user_id)
    db_session.add(task)
    db_session.commit()

    response = client.get(f"/api/tasks/{task.task_id}")
    assert response.status_code == 200
    data = response.get_json()
    assert data["title"] == "Fetch Me"


def test_update_task_api(client, db_session, test_user):
    login_test_user(client, test_user)
    task = Task(title="Old Title", user_id=test_user.user_id)
    db_session.add(task)
    db_session.commit()

    update_payload = {"title": "Updated", "status": "in_progress"}
    response = client.put(f"/api/tasks/{task.task_id}", data=json.dumps(update_payload), content_type="application/json")
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"]


def test_delete_task_api(client, db_session, test_user):
    login_test_user(client, test_user)
    task = Task(title="To Delete", user_id=test_user.user_id)
    db_session.add(task)
    db_session.commit()

    response = client.delete(f"/api/tasks/{task.task_id}")
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"]


def test_get_tasks_by_user_api(client, db_session, test_user):
    login_test_user(client, test_user)
    task1 = Task(title="U1", user_id=test_user.user_id)
    task2 = Task(title="U2", user_id=test_user.user_id)
    db_session.add_all([task1, task2])
    db_session.commit()

    response = client.get(f"/api/users/{test_user.user_id}/tasks")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) >= 2


def test_get_unassigned_tasks_api(client, db_session, test_user):
    login_test_user(client, test_user)
    task = Task(title="Unassigned", user_id=test_user.user_id, project_id=None)
    db_session.add(task)
    db_session.commit()

    response = client.get("/api/tasks/unassigned")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert any(t["title"] == "Unassigned" for t in data)
