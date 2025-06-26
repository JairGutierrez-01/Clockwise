from datetime import datetime

import pytest

from backend.models import (
    User,
    Team,
    Project,
    Task,
)
from backend.models.project import ProjectType, ProjectStatus
from backend.services.project_service import (
    calculate_time_limit_from_credits,
    create_project,
    get_project,
    delete_project,
    update_project,
    update_total_duration_for_project,
    serialize_projects,
    get_info,
    export_project_info_pdf,
    export_project_info_csv,
)


@pytest.fixture
def setup_project_env(db_session):
    user = User(username="projtuser", email="projt@example.com", password_hash="secret")
    team = Team(name="MyTeam")
    db_session.add_all([user, team])
    db_session.commit()
    return user, team


def test_calculate_time_limit_from_credits():
    assert calculate_time_limit_from_credits(2) == 60
    assert calculate_time_limit_from_credits(0) == 0


def test_create_project_individual(db_session, setup_project_env):
    user, _ = setup_project_env
    result = create_project(
        name="Solo",
        description="Test Desc",
        user_id=user.user_id,
        team_id=None,
        time_limit_hours=10,
        due_date=datetime(2025, 5, 1),
        type=ProjectType.IndividualProject,
        is_course=False,
        status=ProjectStatus.InProgress,
    )
    assert result["success"]
    project = Project.query.get(result["project_id"])
    assert project.name == "Solo"
    assert project.team_id is None


def test_create_project_course_calculates_time_limit(db_session, setup_project_env):
    user, _ = setup_project_env
    result = create_project(
        name="CourseProject",
        description="Course Desc",
        user_id=user.user_id,
        team_id=None,
        time_limit_hours=0,
        due_date=datetime(2025, 10, 10),
        type=ProjectType.IndividualProject,
        is_course=True,
        credit_points=3,
        status=ProjectStatus.NotStarted,
    )
    project = Project.query.get(result["project_id"])
    assert project.time_limit_hours == 90


def test_get_project_success(db_session, setup_project_env):
    user, _ = setup_project_env
    p = Project(
        name="FetchMe",
        user_id=user.user_id,
        type=ProjectType.IndividualProject,
        status=ProjectStatus.Completed,
    )
    db_session.add(p)
    db_session.commit()
    result = get_project(p.project_id)
    assert result["success"]
    assert result["project"].name == "FetchMe"


def test_get_project_not_found():
    result = get_project(9999)
    assert result["error"] == "Project not found."


def test_delete_project_success(db_session, setup_project_env):
    user, _ = setup_project_env
    p = Project(
        name="DeleteMe",
        user_id=user.user_id,
        type=ProjectType.TeamProject,
        status=ProjectStatus.Archived,
    )
    db_session.add(p)
    db_session.commit()
    result = delete_project(p.project_id)
    assert result["success"]
    assert Project.query.get(p.project_id) is None


def test_delete_project_not_found():
    result = delete_project(12345678)
    assert result["error"] == "Project not found."


def test_update_project_fields(db_session, setup_project_env):
    user, _ = setup_project_env
    p = Project(
        name="OldName",
        user_id=user.user_id,
        type=ProjectType.IndividualProject,
        status=ProjectStatus.NotStarted,
    )
    db_session.add(p)
    db_session.commit()

    result = update_project(
        p.project_id, {"name": "NewName", "credit_points": 3, "status": "Completed"}
    )
    updated = Project.query.get(p.project_id)
    assert updated.name == "NewName"
    assert updated.time_limit_hours == 90
    assert updated.status == ProjectStatus.Completed


def test_update_project_not_found():
    result = update_project(99999, {"name": "Nothing"})
    assert result["error"] == "Project not found."


def test_update_total_duration(db_session, setup_project_env):
    user, _ = setup_project_env
    p = Project(
        name="TimeSum",
        user_id=user.user_id,
        type=ProjectType.TeamProject,
        status=ProjectStatus.InProgress,
    )
    db_session.add(p)
    db_session.commit()

    task1 = Task(project_id=p.project_id, total_duration_seconds=3600)
    task2 = Task(project_id=p.project_id, total_duration_seconds=1800)
    db_session.add_all([task1, task2])
    db_session.commit()

    result = update_total_duration_for_project(p.project_id)
    assert result["success"]
    assert result["current_hours"] == 1.5
    assert Project.query.get(p.project_id).current_hours == 1.5


def test_serialize_projects_structure(db_session, setup_project_env):
    user, _ = setup_project_env
    p = Project(
        name="SerializeMe",
        user_id=user.user_id,
        type=ProjectType.IndividualProject,
        status=ProjectStatus.InProgress,
    )
    db_session.add(p)
    db_session.commit()

    serialized = serialize_projects([p])
    assert isinstance(serialized, list)
    assert serialized[0]["project_id"] == p.project_id
    assert serialized[0]["status"] == "InProgress"


def test_get_info_returns_own_and_team_projects(
    db_session, setup_project_env, monkeypatch, test_app
):
    user, team = setup_project_env

    # Make current_user mockable
    monkeypatch.setattr("backend.services.project_service.current_user", user)

    own_proj = Project(
        name="OwnProj",
        user_id=user.user_id,
        type=ProjectType.IndividualProject,
        status=ProjectStatus.InProgress,
    )
    db_session.add(own_proj)
    db_session.commit()

    team_proj = Project(
        name="TeamProj",
        user_id=9999,
        team_id=team.team_id,
        type=ProjectType.TeamProject,
        status=ProjectStatus.Archived,
    )
    db_session.add(team_proj)
    db_session.commit()

    from backend.models import UserTeam

    db_session.add(UserTeam(user_id=user.user_id, team_id=team.team_id))
    db_session.commit()

    result = get_info()
    assert "own_projects" in result
    assert "team_projects" in result
    assert any(p["name"] == "OwnProj" for p in result["own_projects"])
    assert any(p["name"] == "TeamProj" for p in result["team_projects"])


def test_export_project_info_pdf_bytes(db_session, setup_project_env):
    user, _ = setup_project_env
    dummy_data = {
        "own_projects": [
            {
                "name": "Test PDF",
                "description": "Desc",
                "due_date": "2025-12-12",
                "status": "InProgress",
                "tasks": [
                    {
                        "title": "PDF Task",
                        "status": "open",
                        "due_date": "2025-12-12",
                        "time_entries": [
                            {
                                "time_entry_id": 1,
                                "start_time": "2025-12-01T10:00:00",
                                "end_time": "2025-12-01T11:00:00",
                                "duration_seconds": 3600,
                                "user_id": user.user_id,
                            }
                        ],
                    }
                ],
            }
        ],
        "team_projects": [],
    }

    content = export_project_info_pdf(dummy_data)
    assert isinstance(content, bytes)
    assert content.startswith(b"%PDF")


def test_export_project_info_csv_format():
    data = {
        "own_projects": [
            {
                "id": 1,
                "name": "CSVProj",
                "description": "Description",
                "status": "InProgress",
                "tasks": [
                    {
                        "title": "Task1",
                        "status": "open",
                        "due_date": "2025-12-12",
                        "time_entries": [
                            {
                                "start_time": "2025-12-01T10:00:00",
                                "end_time": "2025-12-01T11:00:00",
                                "duration_seconds": 3600,
                                "user_id": 1,
                                "time_entry_id": 1,
                            }
                        ],
                    }
                ],
            }
        ],
        "team_projects": [],
    }

    csv_text = export_project_info_csv(data)
    assert "Projekt" in csv_text
    assert "CSVProj" in csv_text
    assert "Task1" in csv_text
    assert "3600" in csv_text
