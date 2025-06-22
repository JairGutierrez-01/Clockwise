from backend.models import UserTeam, Team
from backend.models.project import Project, ProjectType, ProjectStatus
from flask_login import current_user, login_required
from io import BytesIO
from backend.database import db
from datetime import datetime
from flask import (
    Blueprint,
    request,
    redirect,
    url_for,
    render_template,
    send_file,
    make_response,
)
from backend.services.project_service import (
    create_project,
    get_project,
    delete_project,
    update_project,
    get_info,
    export_project_info_csv,
    export_project_info_pdf,
)

#import the service function with a new name
from backend.services.project_service import create_project as service_create_project

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
        status_str = form.get("status")
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

        try:
            status_enum = ProjectStatus[status_str]
        except KeyError:
            return "Ungültiger Status", 400

        result = create_project(
            name=name,
            description=description,
            user_id=current_user.user_id,
            team_id=team_id,
            time_limit_hours=time_limit_hours,
            due_date=due_date,
            type=type_enum,
            is_course=is_course,
            status=status_enum,
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
    """
    Delete a project by ID.

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
        status_str = data.get("status")
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

        try:
            status_ = ProjectStatus[status_str]
        except KeyError:
            return {"error": "Invalid status"}, 400

        result = service_create_project(
            name=name,
            description=description,
            user_id=current_user.user_id,
            team_id=team_id,
            time_limit_hours=time_limit_hours,
            due_date=due_date,
            type=type_,
            status= status_,
            is_course=False,
            credit_points=None
        )
        if result.get("success"):
            return {"project_id": result["project_id"]}, 200
        return {"error": result.get("error", "Project creation failed")}, 400

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

    show_status = request.args.get("status")
    if show_status:
        try:
            status_enum = ProjectStatus[show_status]
            all_projects = [p for p in all_projects if p.status == status_enum]
        except KeyError:
            return {"error": "Invalid status filter"}, 400

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
                "status": p.status.name if hasattr(p.status, "name") else str(p.status),
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
        if "status" in data:
            try:
                project.status = ProjectStatus[data["status"]]
            except KeyError:
                return {"error": "Invalid status value"}, 400
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

@project_bp.route("/api/projects/export/projects/pdf", methods=["GET"])
@login_required
def export_projects_pdf():
    projects_data = get_info()
    print("Exported project info:", projects_data)
    pdf_bytes = export_project_info_pdf(projects_data)

    return send_file(
        BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name="projects.pdf",
    )

@project_bp.route("/api/projects/export/projects/csv", methods=["GET"])
@login_required
def export_projects_csv():
    projects_data = get_info()
    print("Exported project info:", projects_data)
    csv_text = export_project_info_csv(projects_data)

    response = make_response(csv_text)
    response.headers["Content-Disposition"] = "attachment; filename=projects.csv"
    response.headers["Content-Type"] = "text/csv"
    return response


