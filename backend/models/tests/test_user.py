import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database import Base

from datetime import datetime

from backend.models import User
from backend.models import UserTeam
from backend.models import Team
from backend.models import Project
from backend.models import Task
from backend.models import TimeEntry
from backend.models import Notification
from backend.models import Category


@pytest.fixture(scope="function")
def db_session():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_create_user(db_session):
    user = User(
        username="annadoe",
        email="annadoe@example.com",
        password_hash="hashedpassword123",
        first_name="Anna",
        last_name="Doe",
        profile_picture=None
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
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
