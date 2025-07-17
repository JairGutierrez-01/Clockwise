import pytest
from flask_jwt_extended import create_access_token
from datetime import datetime


from backend.models import Notification, User


@pytest.fixture
def setup_notifications(db_session):
    user = User(
        username="notifyuser",
        email="notify@example.com",
        password_hash="hashed",
        first_name="Test",
        last_name="User",
        created_at=datetime.utcnow(),
        last_active=datetime.utcnow(),
        profile_picture=None
    )
    db_session.add(user)
    db_session.commit()

    n1 = Notification(
        user_id=user.user_id, message="You were added", type="team", is_read=False
    )
    n2 = Notification(
        user_id=user.user_id,
        message="New project assigned",
        type="project",
        is_read=True,
    )
    db_session.add_all([n1, n2])
    db_session.commit()

    return user, [n1, n2]

def login_test_user(client, user):
    with client.session_transaction() as session:
        session["_user_id"] = str(user.user_id)

def test_get_notifications(client, db_session, setup_notifications):
    user, _ = setup_notifications
    login_test_user(client, user)

    response = client.get("/notifications")

    assert response.status_code == 200
    data = response.get_json() or []
    assert len(data) == 2
    assert all("message" in n for n in data)

def test_get_only_unread_notifications(client, db_session, setup_notifications):
    user, notifications = setup_notifications
    token = create_access_token(identity=user.user_id)

    response = client.get(
        "/notifications?unread=true",
        headers={"Authorization": f"Bearer {token}"},
        follow_redirects=True
    )

    assert response.status_code == 200
    data = response.get_json() or []
    assert len(data) == 1
    assert data[0].get("is_read") is False

def test_mark_notification_as_read(client, db_session, setup_notifications):
    user, notifications = setup_notifications
    unread_notification = notifications[0]

    response = client.post(
        f"/read/{unread_notification.id}",
        headers={"Authorization": f"Bearer {create_access_token(identity=user.user_id)}"},
        follow_redirects=True
    )
    assert response.status_code in [200, 302]
    db_session.refresh(unread_notification)
    assert unread_notification.is_read is True

def test_mark_already_read_notification(client, db_session, setup_notifications):
    user, notifications = setup_notifications
    already_read = notifications[1]

    response = client.post(
        f"/read/{already_read.id}",
        headers={"Authorization": f"Bearer {create_access_token(identity=user.user_id)}"},
        follow_redirects=True
    )
    assert response.status_code in [200, 302]
    assert b"Already marked as read" in response.data or response.is_json

def test_delete_notification(client, db_session, setup_notifications):
    user, notifications = setup_notifications
    to_delete = notifications[0]

    response = client.post(
        f"/delete/{to_delete.id}",
        headers={"Authorization": f"Bearer {create_access_token(identity=user.user_id)}"},
        follow_redirects=True
    )
    assert response.status_code in [200, 302]
    assert Notification.query.get(to_delete.id) is None

def test_delete_nonexistent_notification(client, db_session, setup_notifications):
    user, _ = setup_notifications

    response = client.post(
        "/delete/999999",
        headers={"Authorization": f"Bearer {create_access_token(identity=user.user_id)}"},
        follow_redirects=True
    )
    assert response.status_code == 404

