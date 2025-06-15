import pytest

from backend.models import User, Team, UserTeam
from backend.services.user_team_service import add_member, delete_member


@pytest.fixture
def setup_test_data(db_session):
    user = User(
        username="testuser",
        email="<EMAIL>",
        first_name="John",
        last_name="Doe",
        password_hash="password",
    )
    team = Team(name="testteam")
    db_session.add(user)
    db_session.add(team)
    db_session.commit()
    return user, team


def test_add_member_success(db_session, setup_test_data, monkeypatch):
    user, team = setup_test_data

    monkeypatch.setattr(
        "backend.services.notifications.notify_user_added_to_team", lambda *a, **k: None
    )

    result = add_member(user.username, team.name, "member")
    assert result["success"] is True
    assert "Member was added successfully" in result["message"]

    user_team = UserTeam.query.filter_by(
        user_id=user.user_id, team_id=team.team_id
    ).first()
    assert user_team is not None
    assert user_team.role == "member"


def test_add_member_user_not_exist(db_session, setup_test_data):
    _, team = setup_test_data
    result = add_member("nonexistentuser", team.name, "member")
    assert "error" in result
    assert result["error"] == "Username doesn't exists."


def test_add_member_team_not_exist(db_session, setup_test_data):
    user, _ = setup_test_data
    result = add_member(user.username, "nonexistentteam", "member")
    assert "error" in result
    assert result["error"] == "Team doesn't exists."


def test_add_member_already_member(db_session, setup_test_data, monkeypatch):
    user, team = setup_test_data
    monkeypatch.setattr(
        "backend.services.notifications.notify_user_added_to_team", lambda *a, **k: None
    )

    add_member(user.username, team.name, "member")

    result = add_member(user.username, team.name, "member")
    assert "error" in result
    assert result["error"] == "User is already a member of this team."


def test_delete_member_success(db_session, setup_test_data):
    user, team = setup_test_data
    add_member(user.username, team.name, "member")

    result = delete_member(user.username, team.name)
    assert result["success"] is True
    assert "Member was removed successfully" in result["message"]

    user_team = UserTeam.query.filter_by(
        user_id=user.user_id, team_id=team.team_id
    ).first()
    assert user_team is None


def test_delete_member_user_not_exist(db_session, setup_test_data):
    _, team = setup_test_data
    result = delete_member("nonexistentuser", team.name)
    assert "error" in result
    assert result["error"] == "Username doesn't exist."


def test_delete_member_team_not_exist(db_session, setup_test_data):
    user, _ = setup_test_data
    result = delete_member(user.username, "nonexistentteam")
    assert "error" in result
    assert result["error"] == "Team doesn't exist."


def test_delete_member_not_member(db_session, setup_test_data):
    user, team = setup_test_data
    result = delete_member(user.username, team.name)
    assert "error" in result
    assert result["error"] == "User is not a member of this team."
