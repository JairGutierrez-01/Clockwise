# tests/test_team_service.py

import pytest
from datetime import datetime

from backend.models import User, Team, UserTeam, Project, Task
from backend.services.team_service import (
    create_new_team,
    check_admin,
    is_team_member,
    get_user_teams,
    remove_member_from_team,
    get_team_members,
    delete_team_and_related,
    get_teams,
)


@pytest.fixture
def setup_user_team(db_session):
    user = User(
        username="notifyuser",
        email="notify@example.com",
        password_hash="hashed",
        first_name="Test",
        last_name="User",
        created_at=datetime.utcnow(),
        last_active=datetime.utcnow(),
        profile_picture=None
    )
    db_session.add(user)
    db_session.commit()
    return user


def test_create_new_team_success(db_session, setup_user_team):
    user = setup_user_team

    result = create_new_team("Alpha Team", user.user_id)

    assert "team_id" in result
    assert result["message"] == "Team created"

    team = Team.query.get(result["team_id"])
    assert team is not None
    assert team.name == "Alpha Team"

    rel = UserTeam.query.filter_by(user_id=user.user_id, team_id=team.team_id).first()
    assert rel is not None
    assert rel.role == "admin"


def test_check_admin_and_member(db_session, setup_user_team):
    user = setup_user_team
    team = Team(name="Beta")
    db_session.add(team)
    db_session.commit()

    db_session.add(UserTeam(user_id=user.user_id, team_id=team.team_id, role="admin"))
    db_session.commit()

    assert check_admin(user.user_id, team.team_id) is not None
    assert is_team_member(user.user_id, team.team_id) is not None


def test_get_user_teams_returns_correct_structure(db_session, setup_user_team):
    user = setup_user_team
    team = Team(name="Gamma")
    db_session.add(team)
    db_session.commit()

    db_session.add(UserTeam(user_id=user.user_id, team_id=team.team_id, role="member"))
    db_session.commit()

    teams = get_user_teams(user.user_id)

    assert isinstance(teams, list)
    assert teams[0]["team_name"] == "Gamma"
    assert teams[0]["role"] == "member"


def test_remove_member_from_team(db_session, setup_user_team):
    user = setup_user_team
    team = Team(name="Delta")
    db_session.add(team)
    db_session.commit()

    rel = UserTeam(user_id=user.user_id, team_id=team.team_id, role="member")
    db_session.add(rel)
    db_session.commit()

    result = remove_member_from_team(user.user_id, team.team_id)
    assert result is True

    assert (
        UserTeam.query.filter_by(user_id=user.user_id, team_id=team.team_id).first()
        is None
    )


def test_get_team_members_returns_list(db_session, setup_user_team):
    user = setup_user_team
    team = Team(name="Epsilon")
    db_session.add(team)
    db_session.commit()

    db_session.add(UserTeam(user_id=user.user_id, team_id=team.team_id, role="admin"))
    db_session.commit()

    members = get_team_members(team.team_id)

    assert isinstance(members, list)
    assert members[0]["user_id"] == user.user_id
    assert members[0]["role"] == "admin"


def test_delete_team_and_related(db_session, setup_user_team):
    user = setup_user_team
    team = Team(name="Zeta")
    db_session.add(team)
    db_session.commit()

    db_session.add(UserTeam(user_id=user.user_id, team_id=team.team_id))
    project = Project(name="ZetaProject", user_id=user.user_id, team_id=team.team_id, time_limit_hours=10)
    db_session.add(project)
    db_session.commit()

    db_session.add(Task(title="Cleanup", project_id=project.project_id))
    db_session.commit()

    deleted = delete_team_and_related(team.team_id)
    assert deleted is True
    assert Team.query.get(team.team_id) is None
    assert Project.query.filter_by(team_id=team.team_id).first() is None
    assert Task.query.filter_by(project_id=project.project_id).first() is None


def test_get_teams_with_projects(db_session, setup_user_team):
    user = setup_user_team

    team = Team(name="TeamWithProjects")
    db_session.add(team)
    db_session.commit()

    db_session.add(UserTeam(user_id=user.user_id, team_id=team.team_id, role="member"))
    db_session.commit()

    project1 = Project(name="P1", team_id=team.team_id, user_id=user.user_id, time_limit_hours=10)
    project2 = Project(name="P2", team_id=team.team_id, user_id=user.user_id, time_limit_hours=10)
    db_session.add_all([project1, project2])
    db_session.commit()

    result = get_teams(user.user_id)

    assert len(result) == 1
    assert result[0]["team_name"] == "TeamWithProjects"
    assert result[0]["role"] == "member"
    assert len(result[0]["projects"]) == 2
    assert {p.name for p in result[0]["projects"]} == {"P1", "P2"}


def test_check_admin_true_and_false(db_session, setup_user_team):
    user = setup_user_team

    team = Team(name="AdminCheck")
    db_session.add(team)
    db_session.commit()

    # First: not admin
    db_session.add(UserTeam(user_id=user.user_id, team_id=team.team_id, role="member"))
    db_session.commit()

    assert check_admin(user.user_id, team.team_id) is None

    # Update to admin
    UserTeam.query.filter_by(user_id=user.user_id, team_id=team.team_id).update(
        {"role": "admin"}
    )
    db_session.commit()

    assert check_admin(user.user_id, team.team_id) is not None
