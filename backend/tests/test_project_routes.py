import pytest
from datetime import datetime

from backend.models import User, Team, Project, UserTeam
from backend.models.project import ProjectType, ProjectStatus


@pytest.fixture
def setup_project_test_data(db_session):
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
    team = Team(name="Project Team")
    db_session.add_all([user, team])
    db_session.commit()
    return user, team


def test_create_project_route(client, db_session, setup_project_test_data, login_user):
    user, team = setup_project_test_data
    db_session.add(UserTeam(user_id=user.user_id, team_id=team.team_id, role="admin"))
    db_session.commit()

    with client.session_transaction() as sess:
        sess["user_id"] = login_user.user_id

    form_data = {
        "name": "New Project",
        "description": "Description",
        "type": "TeamProject",
        "status": "active",
        "due_date": "2025-12-01",
        "time_limit_hours": "10",
        "is_course": "on",
        "credit_points": "5",
        "team_id": str(team.team_id),
    }

    response = client.post("/project/create", data=form_data, follow_redirects=False)

    assert response.status_code in (302, 200), response.get_data(as_text=True)
    project = Project.query.filter_by(name="New Project").first()
    assert project is not None
    assert project.team_id == team.team_id


def test_view_project(client, db_session, setup_project_test_data, login_user):
    db_session.rollback()
    user, _ = setup_project_test_data

    project = Project(
        name="ViewMe",
        user_id=user.user_id,
        type=ProjectType.SoloProject,
        status=ProjectStatus.active,
    )
    db_session.add(project)
    db_session.commit()

    response = client.get(f"/project/{project.project_id}")
    assert response.status_code == 200


def test_delete_project_route(client, db_session, setup_project_test_data, login_user):
    db_session.rollback()
    user, _ = setup_project_test_data

    project = Project(
        name="DeleteMe",
        user_id=user.user_id,
        type=ProjectType.SoloProject,
        status=ProjectStatus.active,
    )
    db_session.add(project)
    db_session.commit()

    response = client.post(
        f"/project/delete/{project.project_id}", follow_redirects=True
    )

    assert response.status_code in (200, 302)
    assert Project.query.get(project.project_id) is None


def test_edit_project_route(client, db_session, setup_project_test_data, login_user):
    db_session.rollback()
    user, _ = setup_project_test_data

    project = Project(
        name="Editable",
        user_id=user.user_id,
        type=ProjectType.SoloProject,
        status=ProjectStatus.active,
    )
    db_session.add(project)
    db_session.commit()

    response = client.post(
        f"/project/edit/{project.project_id}",
        data={"name": "Edited Project", "description": "Updated"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    updated = Project.query.get(project.project_id)
    assert updated.name == "Edited Project"


def test_api_projects(client, db_session, setup_project_test_data, login_user):
    db_session.rollback()
    user, team = setup_project_test_data
    db_session.add(UserTeam(user_id=user.user_id, team_id=team.team_id, role="member"))
    db_session.commit()

    data = {
        "name": "API Project",
        "description": "from API",
        "type": "TeamProject",
        "status": "active",
        "due_date": "01.12.2025",
        "time_limit_hours": 12,
        "team_id": team.team_id,
    }

    post = client.post("/api/projects", json=data)
    assert post.status_code == 200
    assert Project.query.filter_by(name="API Project").first()

    get = client.get("/api/projects")
    assert get.status_code == 200
    json_data = get.get_json()
    assert any(p["name"] == "API Project" for p in json_data["projects"])


def test_api_project_details(client, db_session, setup_project_test_data, login_user):
    db_session.rollback()
    user, team = setup_project_test_data
    db_session.add(UserTeam(user_id=user.user_id, team_id=team.team_id))
    db_session.commit()

    project = Project(
        name="PatchMe",
        user_id=user.user_id,
        team_id=team.team_id,
        type=ProjectType.TeamProject,
        status=ProjectStatus.active,
    )
    db_session.add(project)
    db_session.commit()

    patch = client.patch(
        f"/api/projects/{project.project_id}", json={"name": "Patched Name"}
    )
    assert patch.status_code == 200
    assert Project.query.get(project.project_id).name == "Patched Name"

    delete = client.delete(f"/api/projects/{project.project_id}")
    assert delete.status_code == 200
    assert Project.query.get(project.project_id) is None


def test_export_csv_and_pdf(client, db_session, setup_project_test_data, login_user):
    db_session.rollback()
    user, _ = setup_project_test_data

    pdf = client.get("/api/projects/export/projects/pdf")
    assert pdf.status_code == 200
    assert pdf.headers["Content-Type"] == "application/pdf"

    csv = client.get("/api/projects/export/projects/csv")
    assert csv.status_code == 200
    assert csv.headers["Content-Type"] == "text/csv"
