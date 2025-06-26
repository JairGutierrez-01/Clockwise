from datetime import datetime

import pytest
from sqlalchemy.orm import sessionmaker, scoped_session
from werkzeug.security import generate_password_hash

from app import app as flask_app
from app import db
from backend.models import User
from backend.services.user_service import login_user as login_user_service


@pytest.fixture(scope="session")
def app():
    """Create a Flask application instance for testing.

    This fixture sets up the Flask app with testing configurations,
    initializes the in-memory SQLite database, and provides an
    application context for the duration of the session.

    Yields:
        Flask: The Flask application instance.
    """
    flask_app.config.update(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            "WTF_CSRF_ENABLED": False,
        }
    )

    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.drop_all()


@pytest.fixture()
def db_session(app):
    """Provide a scoped SQLAlchemy session for a test.

    This fixture creates a new database connection and transaction
    for each test. After the test, the transaction is rolled back
    to ensure test isolation.

    Args:
        app (Flask): The Flask app fixture.

    Yields:
        Session: A scoped SQLAlchemy session.
    """
    connection = db.engine.connect()
    transaction = connection.begin()

    session_factory = sessionmaker(bind=connection)
    session = scoped_session(session_factory)

    db.session = session

    yield session

    transaction.rollback()
    connection.close()
    session.remove()


@pytest.fixture()
def client(app):
    """Create a test client for the Flask application.

    This client can be used to simulate HTTP requests to the app.

    Args:
        app (Flask): The Flask app fixture.

    Returns:
        FlaskClient: A test client for the app.
    """
    return app.test_client()


@pytest.fixture()
def runner(app):
    """Provide a CLI runner for the Flask application.

    Useful for testing Flask CLI commands.

    Args:
        app (Flask): The Flask app fixture.

    Returns:
        FlaskCliRunner: A test CLI runner.
    """
    return app.test_cli_runner()


@pytest.fixture
def login_user(db_session):
    """Creates a test user with a hashed password and logs them in."""
    username = "testuser"
    password = "secret123"

    user = User(
        username=username,
        email="test@example.com",
        password_hash=generate_password_hash(password),
        first_name="Test",
        last_name="User",
        created_at=datetime.utcnow(),
        last_active=datetime.utcnow(),
    )
    db_session.add(user)
    db_session.commit()

    # Call your service's login function to verify login works
    result = login_user_service(username=username, password=password)
    assert result["success"], "Login failed in fixture setup"

    return result["user"]
