import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database import Base

from backend.models import User
from backend.models import Team
from backend.models import UserTeam

from datetime import datetime


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


def test_create_user_team(db_session):
    user = User(username="john_doe", email="john@example.com", password_hash="hashedpassword123")
    team = Team(name="Development Team")

    db_session.add(user)
    db_session.add(team)
    db_session.commit()

    assert user.user_id is not None
    assert team.team_id is not None

    user_team = UserTeam(user_id=user.user_id, team_id=team.team_id, role="admin")

    db_session.add(user_team)
    db_session.commit()

    assert user_team.user_id == user.user_id
    assert user_team.team_id == team.team_id
    assert user_team.role == "admin"


def test_user_team_relationship(db_session):
    user = User(username="jane_doe", email="jane@example.com", password_hash="hashedpassword123")
    team = Team(name="Marketing Team")

    db_session.add(user)
    db_session.add(team)
    db_session.commit()

    assert user.user_id is not None
    assert team.team_id is not None

    user_team = UserTeam(user_id=user.user_id, team_id=team.team_id, role="member")

    db_session.add(user_team)
    db_session.commit()

    user_team_from_db = db_session.query(UserTeam).filter_by(user_id=user.user_id, team_id=team.team_id).first()

    assert user_team_from_db is not None
    assert user_team_from_db.user == user
    assert user_team_from_db.team == team
    assert user_team_from_db.role == "member"


def test_default_values(db_session):
    user = User(username="alice_smith", email="alice@example.com", password_hash="hashedpassword123")
    team = Team(name="HR Team")

    db_session.add(user)
    db_session.add(team)
    db_session.commit()

    assert user.user_id is not None
    assert team.team_id is not None

    user_team = UserTeam(user_id=user.user_id, team_id=team.team_id)

    db_session.add(user_team)
    db_session.commit()

    assert user_team.role == "member"