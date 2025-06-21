from datetime import datetime
from io import BytesIO, StringIO

from flask_login import current_user
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import csv
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO
from backend.database import db
from backend.models import Project, Task, Notification, TimeEntry, UserTeam


def calculate_time_limit_from_credits(credit_points):
    """Calculate time limit in hours based on credit points.

    Args:
        credit_points (int): The credit points assigned to the course.

    Returns:
        int: Time limit in hours.
    """
    return credit_points * 30


def create_project(
    name,
    description,
    user_id,
    team_id,
    time_limit_hours,
    due_date,
    type,
    is_course,
    credit_points=None,
):
    """Create a new project and persist it in the database.

    Args:
        name (str): Project name.
        description (str): Project description.
        user_id (int): ID of the user creating the project.
        team_id (int): ID of the associated team.
        time_limit_hours (int): Time limit for the project.
        due_date (datetime): Project deadline.
        type (str): Project type (Solo or Team).
        is_course (bool): Indicates if the project is a course.
        credit_points (int, optional): Credit points if course.

    Returns:
        dict: Success response with project ID or error.
    """
    if is_course and credit_points:
        time_limit_hours = calculate_time_limit_from_credits(int(credit_points))

    # avoid circular import: import when needed
    from backend.services.team_service import create_new_team
    from backend.models.project import ProjectType

    # Automatically create a Team when creating a TeamProject without a team_id
    if type == ProjectType.TeamProject and not team_id:
        team_payload = create_new_team(name=f"{name}", user_id=user_id)
        team_id = team_payload["team_id"]

    new_project = Project(
        name=name,
        description=description,
        user_id=user_id,
        team_id=team_id,
        time_limit_hours=time_limit_hours,
        current_hours=0,
        created_at=datetime.now(),
        due_date=due_date,
        type=type,
        is_course=is_course,
        credit_points=credit_points,
    )

    db.session.add(new_project)
    db.session.commit()

    notification = Notification(
        user_id=user_id,
        project_id=new_project.project_id,
        message=f"Project created '{new_project.name}'.",
        type="project",
    )
    db.session.add(notification)
    db.session.commit()

    return {"success": True, "project_id": new_project.project_id}


def get_project(project_id):
    """GEt a project by its ID.

    Args:
        project_id (int): The unique ID of the project.

    Returns:
        dict: Success and project data or error message.
    """
    project = Project.query.get(project_id)
    if not project:
        return {"error": "Project not found."}
    update_total_duration_for_project(project_id)
    return {"success": True, "project": project}


def delete_project(project_id):
    """Delete a project by its ID.

    Args:
        project_id (int): The unique ID of the project.

    Returns:
        dict: Success message or error if not found.
    """
    project = Project.query.get(project_id)
    if not project:
        return {"error": "Project not found."}

    db.session.delete(project)
    db.session.commit()
    return {"success": True, "message": "Project deleted successfully."}


def update_project(project_id, data):
    """Update a project with provided data.

    Args:
        project_id (int): The unique ID of the project.
        data (dict): Dictionary containing project fields to update.

    Returns:
        dict: Success message or error if not found.
    """
    project = Project.query.get(project_id)
    if not project:
        return {"error": "Project not found."}

    for key, value in data.items():
        if hasattr(project, key):
            if key == "credit_points":
                project.time_limit_hours = calculate_time_limit_from_credits(int(value))
            setattr(project, key, value)

    db.session.commit()
    return {"success": True, "message": "Project updated successfully."}


def update_total_duration_for_project(project_id):
    """
    Recalculate and update the current_hours field of a project
    based on the total durations of all related tasks.

    Args:
        project_id (int): ID of the project to update.

    Returns:
        dict: Success message with updated hours, or error if project not found.
    """
    project = Project.query.get(project_id)
    if not project:
        return {"error": "Project not found"}

    tasks = Task.query.filter_by(project_id=project_id).all()
    total_seconds = sum(
        task.total_duration_seconds or 0
        for task in tasks
        if task.total_duration_seconds is not None
    )

    total_hours = total_seconds / 3600.0

    project.current_hours = round(total_hours, 3)

    db.session.commit()

    return {
        "success": True,
        "project_id": project_id,
        "current_hours": project.current_hours,
    }

def get_info():
    own_projects = Project.query.filter_by(user_id=current_user.user_id).all()

    team_ids = [
        ut.team_id for ut in UserTeam.query.filter_by(user_id=current_user.user_id).all()
    ]

    team_projects = (
        Project.query
        .filter(Project.team_id.in_(team_ids), Project.user_id != current_user.user_id)
        .all()
    )
    def serialize(projects):
        return [
            {
                "project_id": p.project_id,
                "name": p.name,
                "description": p.description,
                "type": p.type.name if hasattr(p.type, "name") else str(p.type),
                "due_date": p.due_date.isoformat() if p.due_date else None,
                "team_id": p.team_id,
            }
            for p in projects
        ]

    return {
        "own_projects": serialize(own_projects),
        "team_projects": serialize(team_projects),
    }

def export_project_info_pdf(data):
    """
    Export detailed project time entry info as PDF Bytes.

    Args:
        data (list of dict): Entries with 'start', 'end', 'task', 'project'

    Returns:
        bytes: PDF data
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)

    y = 750
    c.drawString(30, y, "Eigene Projekte:")
    y -= 20
    for entry in data["own_projects"]:
        c.drawString(30, y, f"{entry['name']} ({entry['due_date'] or 'kein Datum'})")
        y -= 15

    y -= 30
    c.drawString(30, y, "Teamprojekte:")
    y -= 20
    for entry in data["team_projects"]:
        c.drawString(30, y, f"{entry['name']} ({entry['due_date'] or 'kein Datum'})")
        y -= 15

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()

def export_project_info_csv(data):
    """
    Export detailed project time entry info as CSV.

    Args:
        data (list of dict): Entries with 'start', 'end', 'task', 'project'

    Returns:
        str: CSV formatted text
    """
    output = BytesIO()
    writer = csv.writer(output)

    writer.writerow(["Eigene Projekte"])
    writer.writerow(["ID", "Name", "Beschreibung", "Typ", "Fälligkeitsdatum", "Team ID"])
    for p in data["own_projects"]:
        writer.writerow([p["project_id"], p["name"], p["description"], p["type"], p["due_date"], p["team_id"]])

    writer.writerow([])
    writer.writerow(["Teamprojekte"])
    writer.writerow(["ID", "Name", "Beschreibung", "Typ", "Fälligkeitsdatum", "Team ID"])
    for p in data["team_projects"]:
        writer.writerow([p["project_id"], p["name"], p["description"], p["type"], p["due_date"], p["team_id"]])

    output.seek(0)
    return output.getvalue().decode("utf-8")