import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base
from backend.models import Category


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


def test_create_category(db_session):
    """
    Test the creation of a Category instance.

    This test ensures that a Category with a valid name can be added
    to the database and receives an auto-generated ID.

    Args:
        db_session (Session): The database session fixture.
    """
    category = Category(name="Urgent")
    db_session.add(category)
    db_session.commit()

    assert category.category_id is not None
    assert category.name == "Urgent"
