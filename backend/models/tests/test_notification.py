import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database import Base
from backend.models import Notification, User, Project


@pytest.fixture(scope="function")
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_create_notification(db_session):
    """Test creating a Notification with valid user and project references."""
    user = User(username="user1", email="user1@example.com", password_hash="x", first_name="U", last_name="One")
    project = Project(name="P1", description="", time_limit_hours=10, user=user)
    db_session.add_all([user, project])
    db_session.commit()

    note = Notification(
        user_id=user.user_id,
        project_id=project.project_id,
        message="Deadline tomorrow!",
        type="warning"
    )
    db_session.add(note)
    db_session.commit()

    assert note.notification_id is not None
    assert note.is_read is False
    assert note.user == user
    assert note.project == project

"""
def test_notification_creation():
    notif = Notification(
        user_id=1,
        project_id=2,
        message="You were added to the project.",
        type="Uni",
        is_read=False,
        created_at=datetime.now(),
    )

    assert notif.user_id == 1
    assert notif.project_id == 2
    assert notif.message == "You were added to the project."
    assert notif.type == "Uni"
    assert notif.is_read is False
    assert isinstance(notif.created_at, datetime)
"""