import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base
from backend.models import Project, User
from backend.models.project import ProjectType


@pytest.fixture(scope="function")
def db_session():
    """
    Fixture to create a new database session for each test.

    This fixture sets up an in-memory SQLite database for testing and ensures
    that the session is properly closed after the test completes.

    Returns:
        session (Session): A SQLAlchemy session connected to the in-memory database.
    """
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_create_project(db_session):
    """
    Test the creation of a Project instance.

    This test ensures that a Project with required fields can be
    created and committed successfully.

    Args:
        db_session (Session): The database session fixture.
    """
    user = User(
        username="owner",
        email="o@example.com",
        password_hash="x",
        first_name="F",
        last_name="L",
    )
    db_session.add(user)
    db_session.commit()

    project = Project(
        name="Solo Work",
        time_limit_hours=5,
        user_id=user.user_id,
        type=ProjectType.SoloProject,
    )
    db_session.add(project)
    db_session.commit()

    assert project.project_id is not None
    assert project.type == ProjectType.SoloProject


def test_project_repr_and_duration(db_session):
    """
    Test __repr__ and duration_readable property of the Project model.

    This test verifies that the string representation includes a readable duration
    and matches expected structure.

    Args:
        db_session (Session): The database session fixture.
    """
    user = User(
        username="tim",
        email="tim@example.com",
        password_hash="xyz123",
        first_name="Tim",
        last_name="Tester",
    )
    db_session.add(user)
    db_session.commit()

    project = Project(name="New App", time_limit_hours=10, user_id=user.user_id)
    db_session.add(project)
    db_session.commit()

    readable = project.duration_readable
    assert isinstance(readable, str)
    assert "h" in readable

    assert "readable=" in repr(project)
