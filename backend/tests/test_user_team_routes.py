import pytest

from backend.models import User, Team, UserTeam
from backend.services.user_team_service import add_member


@pytest.fixture
def setup_test_data(db_session):
    """Fixture to create and return a test user and team.

    Args:
        db_session (Session): SQLAlchemy test session fixture.

    Returns:
        tuple: A tuple containing the created User and Team instances.
    """
    user = User(
        username="testuser",
        email="<EMAIL>",
        first_name="John",
        last_name="Doe",
        password_hash="password",
    )
    db_session.add(user)

    team = Team(team_id=1, name="Test Team")
    db_session.add(team)

    db_session.commit()
    return user, team


def test_add_member_with_team_id_filter(db_session, setup_test_data, monkeypatch):
    """Test adding a user to a team using username and team name.

    This test checks that the user is correctly associated with the team
    and the membership is saved in the UserTeam table.

    Args:
        db_session (Session): SQLAlchemy test session fixture.
        setup_test_data (tuple): Fixture containing test user and team.
        monkeypatch (MonkeyPatch): Fixture to mock notification function.
    """
    user, team = setup_test_data

    # Mock the notification function to avoid side effects
    monkeypatch.setattr(
        "backend.services.notifications.notify_user_added_to_team", lambda *a, **k: None
    )

    result = add_member(user.username, team.name, "member")

    assert result == {"message": "Member was added successfully", "success": True}

    # Check that the user is now linked to the team
    exists = (
        db_session.query(UserTeam)
        .filter_by(user_id=user.user_id, team_id=team.team_id)
        .first()
        is not None
    )
    assert exists
