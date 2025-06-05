from datetime import datetime

from backend.database import db
from backend.models import Project, Task


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
    category_id,
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
    total_seconds = sum(task.total_duration_seconds or 0 for task in tasks if task.total_duration_seconds is not None)

    total_hours = total_seconds / 3600.0

    project.current_hours = round(total_hours, 3)

    db.session.commit()

    return {
        "success": True,
        "project_id": project_id,
        "current_hours": project.current_hours
    }
