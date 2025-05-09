import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database import Base

from datetime import datetime

from backend.models import User


@pytest.fixture(scope="function")
def db_session():
    """Fixture to create a new database session for each test.

    This fixture sets up an in-memory SQLite database for testing and ensures
    that the session is properly closed after the test completes.

    Returns:
        session (Session): A SQLAlchemy session connected to the in-memory database.
    """
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_create_user(db_session):
    """Test the creation and retrieval of a User.

    This test ensures that a User is correctly created and added to the database.
    It also verifies that the user data can be fetched and matches the inserted values.

    Args:
        db_session (Session): The database session fixture.
    """
    user = User(
        username="annadoe",
        email="annadoe@example.com",
        password_hash="hashedpassword123",
        first_name="Anna",
        last_name="Doe",
        profile_picture=None,
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    fetched_user = db_session.query(User).filter_by(email="annadoe@example.com").first()

    assert fetched_user is not None
    assert fetched_user.user_id is not None
    assert fetched_user.username == "annadoe"
    assert fetched_user.first_name == "Anna"
    assert fetched_user.last_name == "Doe"
    assert fetched_user.password_hash == "hashedpassword123"
    assert fetched_user.created_at <= datetime.now()
    assert fetched_user.profile_picture is None
    assert repr(user).startswith("<User(")
