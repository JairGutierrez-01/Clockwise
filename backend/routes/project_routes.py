from backend.models import UserTeam, Team
from backend.models.project import Project, ProjectType
from backend.models.task import Task
from flask_login import current_user, login_required
from sqlalchemy import and_
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
    update_total_duration_for_project,
)

project_bp = Blueprint("project", __name__)


@project_bp.route("/project/create", methods=["GET", "POST"])
@login_required
def create_project_route():
    """Create a new project.

    Returns:
        Response: Redirect to dashboard on success or form on GET.
    """
    if not current_user.is_authenticated:
        return redirect(url_for("login"))

    admin_teams = (
        db.session.query(UserTeam)
        .filter_by(user_id=current_user.user_id, role="admin")
        .all()
    )
    team_choices = [(ut.team.team_id, ut.team.name) for ut in admin_teams]

    if request.method == "POST":
        form = request.form
        team_id = form.get("team_id")

        if team_id:
            try:
                team_id = int(team_id)
            except ValueError:
                return "Ungültige Team-ID", 400
        else:
            team_id = None

        name = form.get("name")
        description = form.get("description")
        type_str = form.get("type")
        due_date_str = form.get("due_date")
        time_limit_hours = form.get("time_limit_hours")
        is_course = bool(form.get("is_course"))
        credit_points = form.get("credit_points")

        due_date = None
        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, "%Y-%m-%d")
            except ValueError:
                return "Ungültiges Datumsformat", 400

        try:
            type_enum = ProjectType[type_str]
            if type_enum == ProjectType.TeamProject and not team_id:
                return "Ein Team muss für TeamProject ausgewählt werden.", 400
        except KeyError:
            return "Unbekannter Projekttyp", 400

        if team_id:
            team = db.session.get(Team, team_id, name)
            if not team:
                return "Ungültiges Team", 400

            is_admin = UserTeam.query.filter_by(
                user_id=current_user.user_id, team_id=team_id, role="admin"
            ).first()
            if team_id and not is_admin:
                return "Keine Adminrechte für dieses Team", 403

        result = create_project(
            name=name,
            description=description,
            user_id=current_user.user_id,
            team_id=team_id,
            time_limit_hours=time_limit_hours,
            due_date=due_date,
            type=type_enum,
            is_course=is_course,
            credit_points=credit_points,
        )

        if "success" in result:
            return redirect(url_for("dashboard"))

        return result.get("error", "Project creation failed.")

    return render_template("projects.html", team_choices=team_choices)


@project_bp.route("/project/<int:project_id>", methods=["GET"])
@login_required
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
@login_required
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
@login_required
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
@login_required
def api_projects():
    """
    Handle project creation and listing.

    Args:
        None

    Returns:
        dict or tuple: List of user projects or response with project ID or error.
    """
    if request.method == "POST":
        data = request.get_json()
        print("POST /api/projects -> data:", data)

        name = data.get("name")
        description = data.get("description")
        type_str = data.get("type")
        team_id = data.get("team_id") or None
        time_limit_hours = data.get("time_limit_hours")

        due_date = None
        due_date_str = data.get("due_date")
        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, "%d.%m.%Y")
            except ValueError:
                return {"error": "Invalid date format. Use TT.MM.JJJJ."}, 400

        if not name or not type_str:
            return {"error": "Missing fields"}, 400

        try:
            type_ = ProjectType[type_str]
        except KeyError:
            return {"error": f"Unknown project type: {type_str}"}, 400

        if team_id:
            print(
                f"Checking membership: user_id={current_user.user_id}, team_id={team_id}"
            )
            is_member = UserTeam.query.filter_by(
                user_id=current_user.user_id, team_id=team_id
            ).first()
            if not is_member:
                return {"error": "User is not a member of the specified team."}, 403
        else:
            team_id = None

        project = Project(
            name=name,
            description=description,
            type=type_,
            time_limit_hours=time_limit_hours,
            due_date=due_date,
            user_id=current_user.user_id,
            team_id=team_id,
        )

        db.session.add(project)
        db.session.commit()

        return {"project_id": project.project_id}, 201

    team_ids = [
        row.team_id
        for row in UserTeam.query.filter_by(user_id=current_user.user_id).all()
    ]
    own_projects = Project.query.filter(Project.user_id == current_user.user_id)

    if team_ids:
        team_projects = Project.query.filter(Project.team_id.in_(team_ids))
        all_projects = own_projects.union(team_projects).all()
    else:
        all_projects = own_projects.all()

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
                "team_id": p.team_id,
                # Diese 3 Felder extra für FullCalendar:
                "title": p.name,
                "date": p.due_date.strftime("%Y-%m-%d") if p.due_date else None,
                "color": "#f44336",  # oder projektabhängig
            }
            for p in all_projects
        ]
    }


@project_bp.route("/api/projects/<int:project_id>", methods=["PATCH", "DELETE"])
@login_required
def api_project_detail(project_id):
    """
    Modify or delete a specific project.

    Args:
        project_id (int): ID of the project.

    Returns:
        dict: Confirmation of success or error message.
    """
    if not current_user.is_authenticated:
        return {"error": "Not authorized"}, 401

    project = Project.query.filter_by(project_id=project_id).first()

    is_author = project.user_id == current_user.user_id
    is_team_member = (
        project.team_id
        and UserTeam.query.filter_by(
            user_id=current_user.user_id, team_id=project.team_id
        ).first()
    )

    if not (is_author or is_team_member):
        return {"error": "Not authorized"}, 403

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
            due_date_str = data["due_date"]
            if due_date_str:
                try:
                    project.due_date = datetime.strptime(due_date_str, "%d.%m.%Y")
                except ValueError:
                    return {"error": "Invalid date format. Use TT.MM.JJJJ."}, 400

        db.session.commit()
        return {"success": True}

    if request.method == "DELETE":
        db.session.delete(project)
        db.session.commit()
        return {"success": True}


@project_bp.route("/api/available-teams", methods=["GET"])
@login_required
def get_available_teams():
    """
    Get all teams the current user is part of.

    Args:
        None

    Returns:
        dict: List of team objects.
    """
    teams = (
        db.session.query(Team)
        .join(UserTeam, Team.team_id == UserTeam.team_id)
        .filter(UserTeam.user_id == current_user.user_id)
        .all()
    )

    return {
        "teams": [
            {
                "team_id": team.team_id,
                "name": team.name,
                "description": team.description,
            }
            for team in teams
        ]
    }


@project_bp.route("/team-projects", methods=["GET"])
@login_required
def view_team_projects_with_user_tasks():
    """
    Display team projects and only the tasks assigned to the current user.

    Returns:
        Response: Rendered HTML with user's assigned tasks per team project.
    """
    if not current_user.is_authenticated:
        return redirect(url_for("login"))

    user_id = current_user.user_id

    team_ids = [
        ut.team_id for ut in UserTeam.query.filter_by(user_id=user_id).all()
    ]

    if not team_ids:
        return render_template("projects.html", projects=[])

    team_projects = Project.query.filter(Project.team_id.in_(team_ids)).all()

    results = []
    for project in team_projects:
        tasks = Task.query.filter_by(
            project_id=project.project_id,
            assigned_user_id=user_id
        ).all()

        if tasks:
            results.append({"project": project, "tasks": tasks})

    return render_template("projects.html", project_tasks=results)
