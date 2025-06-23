import pytest
from flask_jwt_extended import create_access_token
from backend.models import Notification, User


@pytest.fixture
def setup_notifications(db_session):
    user = User(username="notifyuser", email="notify@example.com", password_hash="hashed")
    db_session.add(user)
    db_session.commit()

    n1 = Notification(user_id=user.user_id, message="You were added", type="team", is_read=False)
    n2 = Notification(user_id=user.user_id, message="New project assigned", type="project", is_read=True)
    db_session.add_all([n1, n2])
    db_session.commit()

    return user, [n1, n2]


def test_get_notifications(client, db_session, setup_notifications, login_user):
    user, notifications = setup_notifications
    login_user(user)
    token = create_access_token(identity=user.user_id)

    response = client.get(
        "/notifications",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 2
    assert all("message" in n for n in data)


def test_get_only_unread_notifications(client, db_session, setup_notifications, login_user):
    user, notifications = setup_notifications
    login_user(user)
    token = create_access_token(identity=user.user_id)

    response = client.get(
        "/notifications?unread=true",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]["is_read"] is False


def test_mark_notification_as_read(client, db_session, setup_notifications, login_user):
    user, notifications = setup_notifications
    login_user(user)

    unread_notification = notifications[0]

    response = client.post(f"/read/{unread_notification.id}")
    assert response.status_code == 200

    db_session.refresh(unread_notification)
    assert unread_notification.is_read is True


def test_mark_already_read_notification(client, db_session, setup_notifications, login_user):
    user, notifications = setup_notifications
    login_user(user)

    already_read = notifications[1]

    response = client.post(f"/read/{already_read.id}")
    assert response.status_code == 200
    assert b"Already marked as read" in response.data


def test_delete_notification(client, db_session, setup_notifications, login_user):
    user, notifications = setup_notifications
    login_user(user)

    to_delete = notifications[0]

    response = client.post(f"/delete/{to_delete.id}")
    assert response.status_code == 302
    assert Notification.query.get(to_delete.id) is None


def test_delete_nonexistent_notification(client, db_session, setup_notifications, login_user):
    user, _ = setup_notifications
    login_user(user)

    response = client.post("/delete/999999")
    assert response.status_code == 404
