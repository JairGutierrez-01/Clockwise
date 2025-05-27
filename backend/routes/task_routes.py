from flask import Blueprint, render_template, request, redirect, url_for
from flask import jsonify
from flask_login import current_user
from datetime import datetime
from backend.services.task_service import (
    create_task,
    get_task_by_id,
    get_task_by_project,
    get_default_tasks,
    update_task,
    delete_task,
)

task_bp = Blueprint("tasks", __name__, url_prefix="/api")


@task_bp.route("/tasks", methods=["GET"])
def get_tasks():
    """
    Return a list of tasks.

    If a project ID is provided via query parameters, only tasks belonging to that
    project are returned. Otherwise, default tasks (without a project) are listed.

    Returns:
        JSON: A list of tasks as dictionaries.
    """
    project_id = request.args.get("project_id")
    if project_id:
        tasks = get_task_by_project(int(project_id))
    else:
        tasks = get_default_tasks()
    return jsonify([task.to_dict() for task in tasks])


@task_bp.route("/tasks", methods=["POST"])
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
    user_id = current_user.user_id if current_user.is_authenticated else None

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
def get_task_by_id_api(task_id):
    """
    Returns the task with the given ID.
    """
    task = get_task_by_id(task_id)
    if task:
        return jsonify(task.to_dict())
    return jsonify({"error": "Task not found"}), 404


@task_bp.route("/tasks/<int:task_id>", methods=["DELETE"])
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
def get_unassigned_tasks():
    """
    Return tasks without project assignment (default tasks).

    Returns:
        JSON: List of unassigned tasks.
    """
    tasks = get_default_tasks()
    return jsonify([task.to_dict() for task in tasks])
