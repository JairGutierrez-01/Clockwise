from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required

from backend.models import Project, UserTeam, Task, Category
from backend.models.task import TaskStatus
from backend.database import db
from backend.services.notifications import notify_task_assigned
from backend.services.task_service import (
    create_task,
    get_task_by_id,
    get_tasks_by_project,
    get_tasks_by_project_for_user,
    update_task,
    delete_task,
    get_unassigned_tasks as get_unassigned_tasks_from_service,
    get_tasks_assigned_to_user
)

task_bp = Blueprint("tasks", __name__)

@task_bp.route("/tasks", methods=["GET"])
@login_required
def get_tasks():
    """
    Return a list of tasks, optionally filtered by project_id or unassigned status.

    Args:
        project_id (int, optional): Filter tasks by project.
        unassigned (bool, optional): Return only tasks without project.

    Returns:
        JSON: List of task objects.
    """
    project_id = request.args.get("project_id")
    unassigned = request.args.get("unassigned")


    if unassigned == "true":
        tasks = get_unassigned_tasks_from_service()
    elif project_id:
        project = Project.query.get(int(project_id))
        if project and project.team_id:
            is_admin = UserTeam.query.filter_by(
                user_id=current_user.user_id,
                team_id=project.team_id,
                role="admin"
            ).first()
            if is_admin:
                tasks = get_tasks_by_project(int(project_id))
            else:
                tasks = get_tasks_by_project_for_user(int(project_id), current_user.user_id)
        else:
            # Solo-Projekt → nur eigene Tasks
            tasks = get_tasks_by_project_for_user(int(project_id), current_user.user_id)
    else:
        tasks = []

    return jsonify([task.to_dict() for task in tasks])


@task_bp.route("/tasks", methods=["POST"])
@login_required
def create_task_api():
    """
    Create a new task.

    Args:
        JSON:
            title (str): Title of the task (optional, defaults to 'Untitled Task').
            description (str, optional): Description of the task.
            category_id (int, optional): ID of the category.
            due_date (str, optional): Due date in 'YYYY-MM-DD' format.
            project_id (int, optional): Project to which the task belongs.
            member_id (int, optional): Assigned team member (only for team projects).
            created_from_tracking (bool, optional): True if created from time tracking.

    Returns:
        JSON: Success message with created task ID or error.
    """
    data = request.get_json()
    print("POST /create_task_api -> data:", data)

    title = data.get("title", "").strip()
    if not title:
        title = "Untitled Task"

    description = data.get("description")
    category_name = data.get("category_name", "").strip()
    category_id = None

    if category_name:
        existing_category = Category.query.filter_by(name=category_name).first()
        if existing_category:
            category_id = existing_category.category_id
        else:
            new_category = Category(name=category_name)
            db.session.add(new_category)
            db.session.commit()
            category_id = new_category.category_id
    member_id = data.get("member_id")
    status = "todo"

    due_date_str = data.get("due_date")
    due_date = None
    if due_date_str:
        try:
            due_date = datetime.strptime(due_date_str, "%Y-%m-%d")
        except ValueError:
            return jsonify({"error": "Invalid date format"}), 400

    project_id = data.get("project_id")
    created_from_tracking = data.get("created_from_tracking", False)

    result = create_task(
        title=title,
        description=description,
        status=status,
        due_date=due_date,
        project_id=project_id,
        member_id=member_id,
        category_id=category_id,
        created_from_tracking=created_from_tracking,
    )

    return jsonify(result), 201


@task_bp.route("/tasks/<int:task_id>", methods=["PUT"])
@login_required
def update_task_api(task_id):
    """
    Update an existing task.

    Args:
        task_id (int): ID of the task to update.
        JSON:
            title (str, optional): New title.
            description (str, optional): New description.
            category_id (int, optional): New category ID.
            status (str, optional): New status (must be a valid TaskStatus).
            due_date (str, optional): New due date in 'YYYY-MM-DD' format.
            project_id (int, optional): New project assignment.

    Returns:
        JSON: Success message with updated task ID or error.
    """
    data = request.get_json()
    print("POST /create_task_api -> data:", data)

    if "due_date" in data and data["due_date"]:
        try:
            data["due_date"] = datetime.strptime(data["due_date"], "%Y-%m-%d")
        except ValueError:
            return jsonify({"error": "Invalid date format"}), 400

    result = update_task(task_id, **data)
    return jsonify(result)


@task_bp.route("/tasks/<int:task_id>", methods=["GET"])
@login_required
def get_task_by_id_api(task_id):
    """
    Retrieve a specific task by ID.

    Args:
        task_id (int): ID of the task to retrieve.

    Returns:
        JSON: Serialized task object or error message.
    """
    task = get_task_by_id(task_id)
    if task:
        return jsonify(task.to_dict())
    return jsonify({"error": "Task not found"}), 404


@task_bp.route("/tasks/<int:task_id>", methods=["DELETE"])
@login_required
def delete_task_api(task_id):
    """
    Delete a task by its ID.

    Args:
        task_id (int): ID of the task to delete.

    Returns:
        JSON: Success or error message.
    """
    result = delete_task(task_id)
    return jsonify(result)


@task_bp.route("/tasks/unassigned", methods=["GET"])
@login_required
def get_unassigned_tasks():
    """
    Retrieve all tasks that are not assigned to any project.

    Returns:
        JSON: List of unassigned task objects.
    """
    tasks = get_unassigned_tasks_from_service()
    task_list = []

    for task in tasks:
        duration_seconds = sum(
            (
                entry.duration_seconds
                if entry.duration_seconds
                   is not None
                else int((entry.duration_minutes or 0) * 60)
            )
            for entry in task.time_entries
        )
        task_dict = task.to_dict()
        total_minutes = duration_seconds // 60
        task_dict["duration_readable"] = (
            f"{total_minutes // 60}h {total_minutes % 60}min"
        )
        task_list.append(task_dict)

    return jsonify(task_list)


@task_bp.route("/users/<int:user_id>/tasks", methods=["GET"])
@login_required
def get_tasks_by_user(user_id):
    """
    Retrieve all tasks assigned to a given user.

    Args:
        user_id (int): User ID to filter by.

    Returns:
        JSON: List of task objects assigned to the user.
    """
    tasks = get_tasks_assigned_to_user(user_id)
    return jsonify([task.to_dict() for task in tasks])


@task_bp.route("/tasks/<int:task_id>/assign", methods=["PATCH"])
def assign_task_to_user_api(task_id):
    """
    Assign or unassign a task to a user.
    Only allowed for team admins.

    Args:
        task_id (int): ID of the task to assign.

    JSON:
        user_id (int or null): ID of the user to assign, or null to unassign.

    Returns:
        JSON: Success or error message.
    """
    if not current_user.is_authenticated:
        return jsonify({"error": "Not authenticated"}), 401

    data = request.get_json()
    user_id = data.get("user_id")
    print("PATCH /assign_task_to_user_api -> data:", data)
    if user_id is not None and not isinstance(user_id, int):
        return jsonify({"error": "Invalid user_id provided. Must be integer or null."}), 400

    task = Task.query.get(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404

    project = Project.query.get(task.project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404

    team_id = project.team_id

    is_admin = UserTeam.query.filter_by(
        user_id=current_user.user_id,
        team_id=team_id,
        role="admin"
    ).first()

    if not is_admin:
        return jsonify({"error": "Only team admins can assign tasks"}), 403
    result = update_task(task_id, member_id=user_id)

    if result.get("success"):
        message = "Task assigned successfully." if user_id is not None else "Task unassigned successfully."

        if user_id is not None:
            notify_task_assigned(
                user_id=user_id,
                task_name=task.title,
                project_name=project.name
            )

        return jsonify({
            "message": message,
            "task_id": task_id,
            "member_id": user_id}), 200

    return jsonify({"error": result.get("error", "Task assignment failed.")}), 400


@task_bp.route("/tasks/<int:task_id>/status", methods=["PATCH"])
@login_required
def update_task_status(task_id):
    """
    Update the status of a task.
    Only allows values defined in TaskStatus enum.

    JSON Input:
        {
            "status": "todo" | "in_progress" | "done"
        }

    Returns:
        JSON: Success message or error.
    """
    if not current_user.is_authenticated:
        return jsonify({"error": "Not authenticated"}), 401

    data = request.get_json()
    new_status = data.get("status", "").lower()

    if new_status not in TaskStatus.__members__:
        return jsonify({
            "error": f"Invalid status: '{new_status}'",
            "allowed_statuses": list(TaskStatus.__members__.keys())
        }), 400

    result = update_task(task_id, status=new_status)

    if result.get("success"):
        return jsonify({
            "message": "Task status updated successfully.",
            "task_id": task_id,
            "status": new_status
        }), 200

    return jsonify({"error": result.get("error", "Status update failed.")}), 400

@task_bp.route("/categories/used", methods=["GET"])
@login_required
def get_used_categories():
    """
    Retrieve all categories that are currently used by at least one task.

    This endpoint returns a list of unique category names that are assigned
    to at least one existing task. Unused categories (i.e., those not assigned
    to any tasks) are excluded.

    Returns:
        JSON:
            {
                "categories": [
                    {"name": "Hausarbeit"},
                    {"name": "Prüfung"},
                    ...
                ]
            }
    """
    categories = (
        db.session.query(Category)
        .join(Task)
        .group_by(Category.category_id)
        .having(db.func.count(Task.task_id) > 0)
        .all()
    )

    return jsonify({
        "categories": [{"name": c.name} for c in categories]
    })
