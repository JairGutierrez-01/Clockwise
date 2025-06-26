import csv
from datetime import datetime
from io import BytesIO
from io import StringIO

from flask_login import current_user
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from backend.database import db
from backend.models import Project, Task, UserTeam
from backend.models.project import ProjectStatus, ProjectType
from backend.services.notification_service import notify_project_created


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
    status,
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
        status (str): Project status (active or inactive).
        is_course (bool): Indicates if the project is a course.
        credit_points (int, optional): Credit points if course.

    Returns:
        dict: Success response with project ID or error.
    """
    if is_course and credit_points:
        time_limit_hours = calculate_time_limit_from_credits(int(credit_points))

    # import here, because otherwise error
    from backend.services.team_service import create_new_team

    # Auto-create a team if project type is TeamProject and no team_id was given.
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
        status=status,
        credit_points=credit_points,
    )

    db.session.add(new_project)
    db.session.commit()

    notify_project_created(user_id, name)

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
            elif key == "status":
                project.status = ProjectStatus(value)
            # Generic update for all other attributes
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


def serialize_projects(projects):
    """
    Serialize a list of Project objects to dicts with nested tasks and time entries.

    Args:
        projects (list): List of Project model instances.

    Returns:
        list: List of serialized project dicts.
    """
    serialized = []
    for p in projects:
        serialized.append(
            {
                "project_id": p.project_id,
                "name": p.name,
                "description": p.description,
                "type": p.type.name if hasattr(p.type, "name") else str(p.type),
                "due_date": p.due_date.isoformat() if p.due_date else None,
                "team_id": p.team_id,
                "status": p.status.name if hasattr(p.status, "name") else str(p.status),
                "tasks": [
                    {
                        "task_id": t.task_id,
                        "title": t.title,
                        "description": t.description,
                        "status": t.status,
                        "due_date": t.due_date.isoformat() if t.due_date else None,
                        "time_entries": [
                            {
                                "time_entry_id": te.time_entry_id,
                                "start_time": te.start_time.isoformat(),
                                "end_time": (
                                    te.end_time.isoformat() if te.end_time else None
                                ),
                                "duration_seconds": te.duration_seconds,
                                "user_id": te.user_id,
                            }
                            for te in t.time_entries
                        ],
                    }
                    for t in p.tasks
                ],
            }
        )
    return serialized


def get_info():
    """
    Get serialized project data for current user and their team projects.

    Returns:
        dict: Dict with 'own_projects' and 'team_projects'.
    """
    own_projects = Project.query.filter_by(user_id=current_user.user_id).all()

    team_ids = [
        ut.team_id
        for ut in UserTeam.query.filter_by(user_id=current_user.user_id).all()
    ]

    team_projects = Project.query.filter(
        Project.team_id.in_(team_ids), Project.user_id != current_user.user_id
    ).all()

    return {
        "own_projects": serialize_projects(own_projects),
        "team_projects": serialize_projects(team_projects),
    }


def export_project_info_pdf(data):
    """
    Generate a PDF summary of projects, tasks, and time entries.

    Args:
        data (dict): Dictionary with 'own_projects' and 'team_projects'.

    Returns:
        bytes: PDF file content as byte string.
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    y = 750  # Position
    x_indent = 30
    min_y = 50

    y -= 10
    c.drawString(x_indent, y, "Eigene Projekte:")
    y -= 20

    for project in data.get("own_projects", []):
        if y < min_y:  # New Site if full
            c.showPage()
            y = 750
        c.drawString(
            x_indent + 10,
            y,
            f"- {project['name']} ({project['due_date'] or 'kein Datum'})",
        )
        y -= 15
        c.drawString(
            x_indent + 15, y, f"Beschreibung: {project.get('description') or '-'}"
        )
        y -= 15
        c.drawString(x_indent + 15, y, f"Status: {project.get('status') or '-'}")
        y -= 15

        for task in project.get("tasks", []):
            if y < min_y:
                c.showPage()
                y = 750
            c.drawString(
                x_indent + 20,
                y,
                f"• Task: {task['title']} [{task['status']}] ({task['due_date'] or 'kein Datum'})",
            )
            y -= 15

            if "time_entries" in task:
                for te in task["time_entries"]:
                    if y < min_y:
                        c.showPage()
                        y = 750
                    c.drawString(
                        x_indent + 30,
                        y,
                        f"◦ TimeEntry: {te['start_time']} - {te['end_time'] or '...'} ({te['duration_seconds']}h)",
                    )
                    y -= 15

    y -= 20
    c.drawString(x_indent, y, "Teamprojekte:")
    y -= 20

    for project in data.get("team_projects", []):
        if y < min_y:
            c.showPage()
            y = 750
        c.drawString(
            x_indent + 10,
            y,
            f"- {project['name']} ({project['due_date'] or 'kein Datum'})",
        )
        y -= 15
        c.drawString(
            x_indent + 15, y, f"Beschreibung: {project.get('description') or '-'}"
        )
        y -= 15
        c.drawString(x_indent + 15, y, f"Status: {project.get('status') or '-'}")
        y -= 15

        for task in project.get("tasks", []):
            if y < min_y:
                c.showPage()
                y = 750
            c.drawString(
                x_indent + 20,
                y,
                f"• Task: {task['title']} [{task['status']}] ({task['due_date'] or 'kein Datum'})",
            )
            y -= 15

            if "time_entries" in task:
                for te in task["time_entries"]:
                    if y < min_y:
                        c.showPage()
                        y = 750
                    c.drawString(
                        x_indent + 30,
                        y,
                        f"◦ TimeEntry: {te['start_time']} - {te['end_time'] or '...'} ({te['duration_seconds']}h))",
                    )
                    y -= 15

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()


def export_project_info_csv(data):
    """
    Export project, task, and time entry info as CSV.

    Args:
        data (dict): Contains 'own_projects' and 'team_projects'.

    Returns:
        str: CSV content as string.
    """
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "Bereich",
            "Projekt",
            "Projektbeschreibung",
            "Projektstatus",
            "Task",
            "Taskstatus",
            "Taskdatum",
            "Start",
            "Ende",
            "Dauer(h)",
        ]
    )

    team_projects = data.get("team_projects") or []
    # Prevent duplicate own projects if they appear also as team projects
    team_project_keys = {(p.get("name"), p.get("id")) for p in team_projects}
    own_projects = [
        p
        for p in data.get("own_projects", [])
        if (p.get("name"), p.get("id")) not in team_project_keys
    ]

    for category, projects in [
        ("Eigene Projekte", own_projects),
        ("Teamprojekte", team_projects),
    ]:
        for project in projects:
            for task in project.get("tasks", []):
                time_entries = task.get("time_entries", [])
                if time_entries:
                    for te in time_entries:
                        writer.writerow(
                            [
                                category,
                                project.get("name"),
                                project.get("description"),
                                project.get("status"),
                                task.get("title"),
                                task.get("status"),
                                task.get("due_date"),
                                te.get("start_time"),
                                te.get("end_time"),
                                te.get("duration_seconds"),
                            ]
                        )
                else:
                    writer.writerow(
                        [
                            category,
                            project.get("name"),
                            project.get("description"),
                            project.get("status"),
                            task.get("title"),
                            task.get("status"),
                            task.get("due_date"),
                            "",
                            "",
                            "",
                            "",
                        ]
                    )

    buffer.seek(0)
    return buffer.read()
