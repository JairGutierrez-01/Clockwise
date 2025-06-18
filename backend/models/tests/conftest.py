import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from backend.database import Base, db


@pytest.fixture(scope="function")
def db_session():
    """Creates a new database session for a test."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    session_factory = sessionmaker(bind=engine)
    session = scoped_session(session_factory)

    # Set the session for the global db object
    db.session = session

    yield session

    session.rollback()
    session.close()
    session.remove()
