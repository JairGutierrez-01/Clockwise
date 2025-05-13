from flask import (
    Blueprint, 
    request, 
    redirect, 
    url_for, 
    render_template
)
from backend.services.project_service import (
    create_project, 
    get_project, 
    delete_project, 
    update_project
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
            category_id=data["category_id"],
            time_limit_hours=data.get("time_limit_hours", 0),
            due_date=data.get("due_date"),
            type=data["type"],
            is_course=bool(data.get("is_course")),
            credit_points=data.get("credit_points")
        )
        if "success" in result:
            return redirect(url_for("dashboard"))
        return result.get("error", "Project creation failed.")

    return render_template("createproject.html")

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
        return render_template("viewproject.html", project=result["project"])
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
        return render_template("editproject.html", project=result["project"])
    return result.get("error", "Project not found."), 404
