from backend.models.project import Project, ProjectType
from flask_login import current_user
from backend.database import db
from datetime import datetime
from flask import (
    Blueprint,
    request,
    redirect,
    url_for,
    render_template,
)
from backend.services.project_service import (
    create_project,
    get_project,
    delete_project,
    update_project,
)

project_bp = Blueprint("project", __name__)


@project_bp.route("/project/create", methods=["GET", "POST"])
def create_project_route():
    """Create a new project.

    Returns:
        Response: Redirect to dashboard on success or form on GET.
    """
    if request.method == "POST":
        data = request.form

        result = create_project(
            name=data["name"],
            description=data.get("description"),
            user_id=data["user_id"],
            team_id=data.get("team_id"),
            time_limit_hours=data.get("time_limit_hours", 0),
            due_date=data.get("due_date"),
            type=data["type"],
            is_course=bool(data.get("is_course")),
            credit_points=data.get("credit_points"),
        )
        if "success" in result:
            return redirect(url_for("dashboard"))
        return result.get("error", "Project creation failed.")

    return render_template("projects.html")


@project_bp.route("/project/<int:project_id>", methods=["GET"])
def view_project(project_id):
    """View a specific project by ID.

    Args:
        project_id (int): ID of the project one wants to view.

    Returns:
        Response: Renders project detail page or error message.
    """
    result = get_project(project_id)
    if "success" in result:
        return render_template("projects.html", project=result["project"])
    return result.get("error", "Project not found."), 404


@project_bp.route("/project/delete/<int:project_id>", methods=["POST"])
def delete_project_route(project_id):
    """Delete a project by ID.

    Args:
        project_id (int): ID of the project to delete.

    Returns:
        Response: Redirect or error.
    """

    result = delete_project(project_id)
    if "success" in result:
        return redirect(url_for("dashboard"))
    return result.get("error", "Delete failed."), 404


@project_bp.route("/project/edit/<int:project_id>", methods=["GET", "POST"])
def edit_project_route(project_id):
    """Edit an existing project by ID.

    Args:
        project_id (int): ID of the project to edit.

    Returns:
        Response: Renders edit form or redirects after update.
    """
    if request.method == "POST":
        data = request.form.to_dict()
        result = update_project(project_id, data)
        if "success" in result:
            return redirect(url_for("dashboard"))
        return result.get("error", "Edit failed.")

    result = get_project(project_id)
    if "success" in result:
        return render_template("projects.html", project=result["project"])
    return result.get("error", "Project not found."), 404


@project_bp.route("/api/projects", methods=["GET", "POST"])
def api_projects():
    if request.method == "POST":
        data = request.get_json()
        name = data.get("name")
        description = data.get("description")
        type_ = ProjectType[data.get("type")]
        time_limit_hours = data.get("time_limit_hours")

        due_date_str = data.get("due_date")
        due_date = None
        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, "%d.%m.%Y")
            except ValueError:
                return {"error": "Invalid date format. Use TT.MM.JJJJ."}, 400

        if not name or not type_:
            return {"error": "Missing fields"}, 400

        project = Project(
            name=name,
            description=description,
            type=type_,
            time_limit_hours=time_limit_hours,
            due_date=due_date,
            user_id=current_user.user_id,
        )

        db.session.add(project)
        db.session.commit()

        return {"project_id": project.project_id}, 201

    projects = Project.query.filter_by(user_id=current_user.user_id).all()
    return {
        "projects": [
            {
                "project_id": p.project_id,
                "name": p.name,
                "description": p.description,
                "type": p.type.name if hasattr(p.type, "name") else str(p.type),
                "time_limit_hours": p.time_limit_hours,
                "current_hours": p.current_hours or 0,
                "duration_readable": p.duration_readable,
                "due_date": p.due_date.isoformat() if p.due_date else None,
                # Diese 3 Felder extra für FullCalendar:
                "title": p.name,
                "date": p.due_date.strftime("%Y-%m-%d") if p.due_date else None,
                "color": "#f44336",  # oder projektabhängig
            }
            for p in projects
        ]
    }


@project_bp.route("/api/projects/<int:project_id>", methods=["PATCH", "DELETE"])
def api_project_detail(project_id):
    if not current_user.is_authenticated:
        return {"error": "Not authorized"}, 401

    project = Project.query.filter_by(
        project_id=project_id, user_id=current_user.user_id
    ).first()
    if not project:
        return {"error": "Project not found"}, 404

    if request.method == "PATCH":
        data = request.get_json()
        if "name" in data:
            project.name = data["name"]
        if "description" in data:
            project.description = data["description"]
        if "type" in data:
            project.type = ProjectType[data["type"]]
        if "time_limit_hours" in data:
            project.time_limit_hours = data["time_limit_hours"]
        if "due_date" in data:
            try:
                project.due_date = datetime.strptime(data["due_date"], "%d.%m.%Y")
            except ValueError:
                return {"error": "Invalid date format. Use TT.MM.JJJJ."}, 400

        db.session.commit()
        return {"success": True}

    if request.method == "DELETE":
        db.session.delete(project)
        db.session.commit()
        return {"success": True}
