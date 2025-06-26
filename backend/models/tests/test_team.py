import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base
from backend.models import Team


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


def test_create_team(db_session):
    """
    Test the creation of a Team instance.

    This test ensures that a Team can be added to the database
    and receives a valid ID and name.

    Args:
        db_session (Session): The database session fixture.
    """
    team = Team(name="SEP Team", description="ClockWise")
    db_session.add(team)
    db_session.commit()

    assert team.team_id is not None
    assert team.name == "SEP Team"


def test_team_is_valid(db_session):
    """
    Test the is_valid() method of the Team model.

    This test checks if the model correctly validates the team name,
    returning False for empty names and True for valid ones.

    Args:
        db_session (Session): The database session fixture.
    """
    team = Team(name="  ")
    assert not team.is_valid()

    team.name = "Valid Team"
    assert team.is_valid()


"""
    team = Team(name="Lineare Algebra")
    assert team.is_valid() is True
"""
