import io

from werkzeug.datastructures import FileStorage

from backend.models import User
from backend.services.user_service import register_user


def test_register_user_success(db_session, client, monkeypatch):
    """Test successful user registration with a profile picture.

    Args:
        db_session (Session): SQLAlchemy test session fixture.
        client (FlaskClient): Flask test client.
        monkeypatch (MonkeyPatch): Fixture to override method behavior.
    """
    fake_image = FileStorage(
        stream=io.BytesIO(b"Hello world!"),
        filename="test.png",
        content_type="image/png",
    )

    def fake_save(path):
        """Simulates image saving without writing to disk."""
        pass

    monkeypatch.setattr(fake_image, "save", fake_save)

    result = register_user(
        username="user",
        email="<EMAIL>",
        first_name="John",
        last_name="Doe",
        password="<PASSWORD>",
        profile_picture=fake_image,
    )

    assert result["success"] is True
    assert User.query.filter_by(username="user").first() is not None


def test_register_user_duplicate(db_session, client):
    """Test registration fails when using an existing username or email.

    Args:
        db_session (Session): SQLAlchemy test session fixture.
        client (FlaskClient): Flask test client.
    """
    user = User(
        username="duplicate",
        email="<EMAIL>",
        password_hash="hashed",
        first_name="John",
        last_name="Doe",
    )
    db_session.add(user)
    db_session.commit()

    result = register_user(
        username="duplicate",
        email="<EMAIL>",
        first_name="John",
        last_name="Doe",
        password="password",
    )

    assert "error" in result
    assert result["error"] == "Username or e-mail already exists."
