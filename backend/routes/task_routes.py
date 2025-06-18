from datetime import datetime

from flask import Blueprint, request
from flask import jsonify
from flask_login import current_user, login_required

from backend.services.task_service import (
    create_task,
    get_task_by_id,
    get_tasks_by_project,
    update_task,
    delete_task,
)
from backend.services.task_service import (
    get_unassigned_tasks as get_unassigned_tasks_from_service,
)
from backend.services.task_service import get_tasks_assigned_to_user

task_bp = Blueprint("tasks", __name__)


@task_bp.route("/tasks", methods=["GET"])
@login_required
def get_tasks():
    """
    Return a list of tasks (optionally filtered by project_id),
    and include duration_hours in the response.

    Query Parameters:
        project_id (int, optional): ID of the project whose tasks should be returned.

    Returns:
        JSON: List of task objects including duration_hours.
    """
    project_id = request.args.get("project_id")
    unassigned = request.args.get("unassigned")

    if unassigned == "true":
        tasks = get_unassigned_tasks_from_service()
    elif project_id:
        tasks = get_tasks_by_project(int(project_id))
    else:
        tasks = []

    task_list = []
    for task in tasks:
        task_dict = task.to_dict()
        task_list.append(task_dict)

    return jsonify(task_list)


@task_bp.route("/tasks", methods=["POST"])
@login_required
def create_task_api():
    """
    Create a new task using a JSON request.

    Expected JSON:
        {
            "title": "Task title",
            "description": "Optional description",
            "category_id": int,
            "due_date": "YYYY-MM-DD",
            "project_id": int,
            "created_from_tracking": bool (optional)
        }

    Returns:
        JSON: Success message with created task ID.
    """
    data = request.get_json()

    title = data.get("title", "").strip()
    if not title:
        title = "Untitled Task"
    description = data.get("description")
    category_id = data.get("category_id")
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
    user_id = data.get("user_id", None)

    if user_id is not None and not isinstance(user_id, int):
        return jsonify({"error": "Invalid user_id provided in creation. Must be integer or null."}), 400

    result = create_task(
        title=title,
        description=description,
        status=status,
        due_date=due_date,
        project_id=project_id,
        user_id=user_id,
        category_id=category_id,
        created_from_tracking=created_from_tracking,
    )

    return jsonify(result), 201


@task_bp.route("/tasks/<int:task_id>", methods=["PUT"])
@login_required
def update_task_api(task_id):
    """
    Edit an existing task via JSON.

    Args:
        task_id (int): ID of the task to edit.

    Expected JSON fields (any subset):
        - title
        - description
        - category_id
        - status
        - due_date (YYYY-MM-DD)
        - project_id

    Returns:
        JSON: Success message with updated task ID or error.
    """
    data = request.get_json()

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
    Returns the task with the given ID.
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
    Return tasks without project assignment (unassigned tasks).

    Returns:
        JSON: List of unassigned tasks.
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


"""New route added just to experiment. Please dont kill me """


@task_bp.route("/users/<int:user_id>/tasks", methods=["GET"])
@login_required
def get_tasks_by_user(user_id):
    """
    Return all tasks assigned to a specific user.
    """
    tasks = get_tasks_assigned_to_user(user_id)
    return jsonify([task.to_dict() for task in tasks])


@task_bp.route("/tasks/<int:task_id>/assign", methods=["PATCH"])
def assign_task_to_user_api(task_id):
    """
    Assigns or unassigns a task to a user.
    Expected JSON: {"user_id": int or null}
    """
    if not current_user.is_authenticated:
        return jsonify({"error": "Not authenticated"}), 401

    data = request.get_json()

    user_id = data.get("user_id")


    if user_id is not None and not isinstance(user_id, int):
        return jsonify({"error": "Invalid user_id provided. Must be integer or null."}), 400

    result = update_task(task_id, user_id=user_id)

    if result.get("success"):
        message = "Task assigned successfully." if user_id is not None else "Task unassigned successfully."
        return jsonify({"message": message, "task_id": task_id, "user_id": user_id}), 200

    return jsonify({"error": result.get("error", "Task assignment failed.")}), 400