from datetime import datetime, timedelta

import pytest

from backend.models import Task, TimeEntry, Project
from backend.models import User, Team
from backend.models.project import ProjectType


@pytest.fixture
def setup_test_data(db_session):
    """
    Creates a test user and a team for analysis-related tests.

    Args:
        db_session (SQLAlchemy.Session): The active database session for committing test data.

    Returns:
        tuple: A tuple containing the created user and team.
    """
    user = User(
        username="testinguser",
        email="testy@example.com",
        first_name="John",
        last_name="Doe",
        password_hash="password",
    )
    db_session.add(user)

    team = Team(team_id=1, name="Test Team")
    db_session.add(team)

    db_session.commit()
    return user, team


@pytest.fixture
def setup_analysis_data(db_session, setup_test_data):
    """
    Sets up a user, project, task, and time entry for analysis-related test cases.

    Args:
        db_session (SQLAlchemy.Session): The active database session.
        setup_test_data (tuple): The user and team from setup_test_data.

    Returns:
        tuple: The created user, project, task, and time entry.
    """
    user, team = setup_test_data

    project = Project(
        name="Testprojekt",
        description="Test description",
        time_limit_hours=10,
        current_hours=3.5,
        created_at=datetime.now(),
        due_date=datetime.now() + timedelta(days=7),
        type=ProjectType.TeamProject,
        is_course=True,
        credit_points=5,
        user_id=user.user_id,
        team_id=team.team_id,
    )
    db_session.add(project)
    db_session.commit()

    task = Task(
        title="Testtask",
        project_id=project.project_id,
        user_id=user.user_id,
        project=project,
    )
    db_session.add(task)
    db_session.commit()

    time_entry = TimeEntry(
        user_id=user.user_id,
        task_id=task.task_id,
        start_time=datetime.now() - timedelta(hours=2),
        end_time=datetime.now(),
    )
    db_session.add(time_entry)
    db_session.commit()

    return user, project, task, time_entry


def test_project_progress(client, setup_analysis_data):
    """
    Tests the /project-progress API endpoint.

    Asserts that the response returns a valid dictionary with status code 200.
    """
    response = client.get("/api/analysis/project-progress")
    assert response.status_code == 200
    assert isinstance(response.get_json(), dict)


def test_actual_vs_planned(client, setup_analysis_data):
    """
    Tests the /actual-vs-planned API endpoint.

    Verifies that each project in the response includes both 'actual' and 'target' values.
    """
    response = client.get("/api/analysis/actual-vs-planned")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)

    for project, values in data.items():
        assert "actual" in values
        assert "target" in values


def test_weekly_time_stacked(client, setup_analysis_data):
    """
    Tests the /weekly-time-stacked API endpoint.

    Verifies the structure of the JSON response and proper handling of valid and invalid date parameters.
    """
    response = client.get("/api/analysis/weekly-time-stacked")
    assert response.status_code == 200
    data = response.get_json()
    assert "labels" in data and "datasets" in data
    assert isinstance(data["labels"], list)
    assert isinstance(data["datasets"], list)

    # Valid date parameter
    response = client.get("/api/analysis/weekly-time-stacked?start=2025-06-22")
    assert response.status_code == 200

    # Invalid date parameter
    response = client.get("/api/analysis/weekly-time-stacked?start=invalid-date")
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_export_pdf(client, setup_analysis_data):
    """
    Tests the /export/pdf API endpoint for time entry export as a PDF file.

    Checks for correct content type, presence of PDF data, and valid response for date filters.
    """
    response = client.get("/api/analysis/export/pdf")
    assert response.status_code == 200
    assert response.content_type == "application/pdf"
    assert len(response.data) > 0
    assert response.data[:4] == b"%PDF"

    # With date range
    response = client.get("/api/analysis/export/pdf?start=2025-06-01&end=2025-06-30")
    assert response.status_code == 200

    # Invalid date format
    response = client.get("/api/analysis/export/pdf?start=invalid&end=invalid")
    assert response.status_code == 400


def test_export_csv(client, setup_analysis_data):
    """
    Tests the /export/csv API endpoint for time entry export as a CSV file.

    Verifies headers, file content, response type, and error handling for date parameters.
    """
    response = client.get("/api/analysis/export/csv")
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "text/csv"
    assert (
        "attachment; filename=time_entries.csv"
        in response.headers["Content-Disposition"]
    )
    assert response.data  # CSV content is not empty

    # With date range
    response = client.get("/api/analysis/export/csv?start=2025-06-01&end=2025-06-30")
    assert response.status_code == 200

    # Invalid date format
    response = client.get("/api/analysis/export/csv?start=invalid&end=invalid")
    assert response.status_code == 400
