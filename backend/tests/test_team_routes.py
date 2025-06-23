import pytest

from backend.models import Team, User, UserTeam


@pytest.fixture
def setup_team_test_data(db_session):
    user = User(username="teamuser", email="user@team.com", password_hash="pass")
    db_session.add(user)
    team = Team(name="Test Team")
    db_session.add(team)
    db_session.commit()
    return user, team


def test_get_user_teams(client, db_session, setup_team_test_data, login_user):
    user, team = setup_team_test_data
    db_session.add(UserTeam(user_id=user.user_id, team_id=team.team_id, role="member"))
    db_session.commit()
    login_user(user)

    response = client.get("/teams/")

    assert response.status_code == 200
    data = response.get_json()
    assert data["current_user"]["user_id"] == user.user_id
    assert any(t["name"] == team.name for t in data["teams"])


def test_create_team(client, db_session, setup_team_test_data, login_user):
    user, _ = setup_team_test_data
    login_user(user)

    response = client.post("/teams/", json={"name": "New Team"})

    assert response.status_code == 201
    data = response.get_json()
    assert "team_id" in data or data.get("success") is True


def test_get_user_details(client, db_session, setup_team_test_data, login_user):
    user, _ = setup_team_test_data
    login_user(user)

    response = client.get(f"/teams/users/{user.user_id}")

    assert response.status_code == 200
    data = response.get_json()
    assert data["user_id"] == user.user_id


def test_add_team_member(client, db_session, setup_team_test_data, login_user):
    admin, team = setup_team_test_data
    member = User(username="member", email="member@x.com", password_hash="pass")
    db_session.add(member)
    db_session.add(UserTeam(user_id=admin.user_id, team_id=team.team_id, role="admin"))
    db_session.commit()
    login_user(admin)

    response = client.patch(
        f"/teams/{team.team_id}/add-member",
        json={"user_id": member.username, "role": "member"},
    )

    assert response.status_code == 200
    assert UserTeam.query.filter_by(
        user_id=member.user_id, team_id=team.team_id
    ).first()


def test_remove_team_member(client, db_session, setup_team_test_data, login_user):
    admin, team = setup_team_test_data
    member = User(username="kickme", email="kick@x.com", password_hash="pass")
    db_session.add(member)
    db_session.add_all(
        [
            UserTeam(user_id=admin.user_id, team_id=team.team_id, role="admin"),
            UserTeam(user_id=member.user_id, team_id=team.team_id, role="member"),
        ]
    )
    db_session.commit()
    login_user(admin)

    response = client.patch(
        f"/teams/{team.team_id}/remove-member", json={"user_id": member.username}
    )

    assert response.status_code == 200
    assert not UserTeam.query.filter_by(
        user_id=member.user_id, team_id=team.team_id
    ).first()


def test_delete_team(client, db_session, setup_team_test_data, login_user):
    admin, team = setup_team_test_data
    db_session.add(UserTeam(user_id=admin.user_id, team_id=team.team_id, role="admin"))
    db_session.commit()
    login_user(admin)

    response = client.delete(f"/teams/{team.team_id}")

    assert response.status_code == 200
    assert Team.query.get(team.team_id) is None


def test_get_team_members(client, db_session, setup_team_test_data, login_user):
    user, team = setup_team_test_data
    db_session.add(UserTeam(user_id=user.user_id, team_id=team.team_id, role="member"))
    db_session.commit()
    login_user(user)

    response = client.get(f"/teams/{team.team_id}/members")

    assert response.status_code == 200
    data = response.get_json()
    assert any(m["user_id"] == user.user_id for m in data)


def test_assign_project_to_team(client, db_session, setup_team_test_data, login_user):
    from backend.models import Project

    admin, team = setup_team_test_data
    db_session.add(UserTeam(user_id=admin.user_id, team_id=team.team_id, role="admin"))
    project = Project(name="Demo", team_id=None)
    db_session.add(project)
    db_session.commit()
    login_user(admin)

    response = client.post(
        f"/teams/{team.team_id}/assign_project", json={"project_id": project.project_id}
    )

    assert response.status_code == 200
    assert Project.query.get(project.project_id).team_id == team.team_id


def test_get_team_tasks(client, db_session, login_user):
    from backend.models import Project, Task

    admin = User(username="admin", email="admin@x.com", password_hash="pass")
    member = User(username="member", email="member@x.com", password_hash="pass")
    db_session.add_all([admin, member])
    db_session.commit()

    team = Team(name="Task Team")
    db_session.add(team)
    db_session.commit()

    db_session.add_all(
        [
            UserTeam(user_id=admin.user_id, team_id=team.team_id, role="admin"),
            UserTeam(user_id=member.user_id, team_id=team.team_id, role="member"),
        ]
    )

    project = Project(name="Test Project", team_id=team.team_id)
    db_session.add(project)
    db_session.commit()

    task_admin = Task(
        title="Admin Task", project_id=project.project_id, member_id=admin.user_id
    )
    task_member = Task(
        title="Member Task", project_id=project.project_id, member_id=member.user_id
    )
    db_session.add_all([task_admin, task_member])
    db_session.commit()

    login_user(admin)
    response = client.get(f"/teams/{team.team_id}/tasks")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 2

    login_user(member)
    response = client.get(f"/teams/{team.team_id}/tasks")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]["title"] == "Member Task"
    assert data[0]["is_mine"] is True
