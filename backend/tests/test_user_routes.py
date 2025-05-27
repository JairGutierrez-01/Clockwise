import io
import pytest
from flask import url_for
from backend.routes import user_routes
from backend.routes.user_routes import auth_bp


def test_register_get(client):
    response = client.get("/auth/register")
    assert response.status_code == 200
    assert b"Register" in response.data


def test_register_post_success(monkeypatch, client):
    def mock_register_user(
        username, email, first_name, last_name, password, profile_picture
    ):
        return {"success": True}

    monkeypatch.setattr("backend.routes.user_routes.register_user", mock_register_user)

    data = {
        "username": "test",
        "email": "<EMAIL>",
        "first_name": "John",
        "last_name": "Doe",
        "password": "<PASSWORD>",
        "profile_picture": (io.BytesIO(b"fake image data"), "test.jpg"),
    }
    response = client.post(
        "/auth/register",
        data=data,
        content_type="multipart/form-data",
        follow_redirects=False,
    )
    assert response.status_code == 302  # Redirect to log in


def test_login_get(client):
    response = client.get("/auth/login")
    assert response.status_code == 200
    assert b"Login" in response.data


def test_login_post_success(monkeypatch, client):
    class MockUser:
        is_authenticated = True

    def mock_login_user(username, password):
        return {"success": True, "user": MockUser()}

    monkeypatch.setattr("backend.routes.user_routes.login_user", mock_login_user)
    monkeypatch.setattr(
        "backend.routes.user_routes.flask_login_user", lambda user: None
    )

    data = {"username": "test", "password": "<PASSWORD>"}
    response = client.post("/auth/login", data=data, follow_redirects=False)
    assert response.status_code == 302  # Redirect to Dashboard


def test_forgot_passwort_post(monkeypatch, client):
    def mock_password_forget(email):
        return {"success": True}

    monkeypatch.setattr(
        "backend.routes.user_routes.password_forget", mock_password_forget
    )
    response = client.post("/auth/forgot-password", data={"email": "test@example.com"})
    assert b"Reset instructions have been sent to your email." in response.data


def test_reset_passwort_token_invalid(monkeypatch, client):
    monkeypatch.setattr("backend.routes.user_routes.new_password", lambda token: None)
    response = client.post(
        "/auth/forgot-password/invalidtoken/1", data={"email": "<EMAIL>"}
    )
    assert b"Token is invalid or expired." in response.data


def test_edit_profile_post_success(monkeypatch, client):
    def mock_edit_profile(
        user_id, username, email, first_name, last_name, password, profile_picture
    ):
        return {"success": True}

    monkeypatch.setattr("backend.routes.user_routes.edit_user", mock_edit_profile)
    data = {
        "username": "test",
        "email": "<EMAIL>",
        "first_name": "John",
        "last_name": "Doe",
        "password": "<PASSWORD>",
        "profile_picture": (io.BytesIO(b"new image data"), "new.jpg"),
    }
    response = client.post(
        "/auth/edit/profile/1",
        data=data,
        content_type="multipart/form-data",
        follow_redirects=False,
    )
    assert response.status_code == 302
