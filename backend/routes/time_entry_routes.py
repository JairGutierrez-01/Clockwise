from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required

from backend.models.time_entry import TimeEntry
from backend.services import time_entry_service
import backend.models.task as task_model
import backend.services.task_service as task_service
from backend.services.task_service import is_user_authorized_for_task
from backend.services.time_entry_service import update_durations_for_task_and_project
from backend.services.time_entry_service import get_latest_project_time_entry_for_user
from backend.services.time_entry_service import (
    create_time_entry,
    get_time_entry_by_id,
    get_time_entries_by_task,
    update_time_entry,
    delete_time_entry,
    start_time_entry,
    stop_time_entry,
    pause_time_entry,
    resume_time_entry,
)
from backend.services.task_service import get_tasks_without_time_entries

time_entry_bp = Blueprint("time_entries", __name__, url_prefix="/api/time_entries")


@time_entry_bp.route("/", methods=["POST"])
@login_required
def create_time_entry_api():
    """
    Create a new time entry manually.

    Expected JSON:
        {
            "task_id": int,
            "start_time": "YYYY-MM-DD HH:MM",
            "end_time": "YYYY-MM-DD HH:MM",
            "duration_seconds": int,
            "comment": "Optional comment"
        }

    Returns:
        JSON response with status or error.
    """
    data = request.get_json()
    user_id = current_user.user_id

    task_id = data.get("task_id")
    if task_id:
        task = task_model.Task.query.get(task_id)
        if not is_user_authorized_for_task(task, user_id):
            return jsonify({"error": "You are not authorized to create time entries for this task"}), 403

    result = create_time_entry(
        user_id=user_id,
        task_id=data.get("task_id"),
        start_time=data.get("start_time"),
        end_time=data.get("end_time"),
        duration_seconds=data.get("duration_seconds"),
        comment=data.get("comment"),
    )
    if result.get("success") and data.get("task_id"):
        update_durations_for_task_and_project(data.get("task_id"))
    return jsonify(result)


@time_entry_bp.route("/<int:entry_id>", methods=["GET"])
@login_required
def get_entry(entry_id):
    """
    Get a single time entry by its ID.

    Args:
        entry_id (int): Time entry ID.

    Returns:
        JSON: Time entry data or error.
    """
    entry = get_time_entry_by_id(entry_id)
    return jsonify(entry.to_dict()) if entry else (jsonify({"error": "Not found"}), 404)


@time_entry_bp.route("/task/<int:task_id>", methods=["GET"])
@login_required
def get_entries_by_task(task_id):
    entries = get_time_entries_by_task(task_id)
    if not entries:
        return jsonify({"error": "No time entries found"}), 404
    return jsonify([e.to_dict() for e in entries]), 200


@time_entry_bp.route("/available-tasks", methods=["GET"])
@login_required
def get_tasks_without_entries():
    """
    Get all tasks that do not have a time entry yet.
    These are shown on the time tracking page.

    Returns:
        JSON: List of available tasks.
    """
    tasks = get_tasks_without_time_entries(current_user.user_id)
    return jsonify([task.to_dict() for task in tasks])


@time_entry_bp.route("/start", methods=["POST"])
@login_required
def start_entry():
    """
    Start a new time entry for a given task or create an untitled task if none provided.

    JSON Payload:
        {
            "task_id": int (optional),
            "comment": str (optional)
        }

    Returns:
        JSON: Success message or error.
    """
    data = request.get_json()
    task_id = data.get("task_id")
    comment = data.get("comment")

    user_id = current_user.user_id if current_user.is_authenticated else None
    if not user_id:
        return jsonify({"error": "Authentication required"}), 401

    # If no task_id is provided or is empty → create new "Untitled Task"
    if not task_id or str(task_id).strip() == "":
        count = task_model.Task.query.filter(
            task_model.Task.user_id == user_id,
            task_model.Task.title.like("Untitled Task%"),
        ).count()

        title = f"Untitled Task #{count + 1}"
        task_result = task_service.create_task(
            title=title,
            created_from_tracking=True
        )
        task_id = task_result["task_id"]

    if task_id:
        task = task_model.Task.query.get(task_id)
        if not task:
            return jsonify({"error": "Task not found"}), 404

        if not is_user_authorized_for_task(task, user_id):
            return jsonify({"error": "You are not authorized to track this task"}), 403

    return jsonify(start_time_entry(user_id=user_id, task_id=task_id, comment=comment))


@time_entry_bp.route("/stop/<int:entry_id>", methods=["POST"])
@login_required
def stop_entry(entry_id):
    """
    Stop a running time entry.

    Args:
        entry_id (int): ID of  the entry to stop.

    Returns:
        JSON: Success message or error.
    """
    time_entry = TimeEntry.query.get(entry_id)

    if time_entry:
        task = time_entry.task
        if not is_user_authorized_for_task(task, current_user.user_id):
            return jsonify({"error": "You are not authorized to stop this time entry"}), 403

    result = stop_time_entry(entry_id)

    # if an error occurs, stop the process
    if not result.get("success"):
        return jsonify(result), 400

    if time_entry and time_entry.task_id:
        update_durations_for_task_and_project(time_entry.task_id)

        from backend.services.project_service import update_total_duration_for_project

        print(">>> MANUELLER TEST START")
        task = time_entry.task
        if task and task.project_id:
            update_total_duration_for_project(task.project_id)
            print(">>> update_total_duration_for_project wurde ausgeführt!")
        else:
            print(">>> Kein Projekt vorhanden – wird übersprungen.")
        print(">>> MANUELLER TEST ENDE")

    return jsonify(result)


@time_entry_bp.route("/pause/<int:entry_id>", methods=["POST"])
@login_required
def pause_entry(entry_id):
    """
    Pause a running time entry.

    Args:
        entry_id (int): ID of the entry to pause.

    Returns:
        JSON: Success message or error.
    """
    time_entry = TimeEntry.query.get(entry_id)

    if time_entry:
        task = time_entry.task
        if not is_user_authorized_for_task(task, current_user.user_id):
            return jsonify({"error": "You are not authorized to pause this time entry"}), 403

    return jsonify(pause_time_entry(entry_id))


@time_entry_bp.route("/resume/<int:entry_id>", methods=["POST"])
@login_required
def resume_entry(entry_id):
    """
    Resume a paused time entry.

    Args:
        entry_id (int): ID of the entry to resume.

    Returns:
        JSON: Success message or error.
    """
    time_entry = TimeEntry.query.get(entry_id)

    if time_entry:
        task = time_entry.task
        if not is_user_authorized_for_task(task, current_user.user_id):
            return jsonify({"error": "You are not authorized to resume this time entry"}), 403

    return jsonify(resume_time_entry(entry_id))


@time_entry_bp.route("/<int:entry_id>", methods=["DELETE"])
@login_required
def delete_entry(entry_id):
    """
    Delete a time entry by its ID.

    Returns:
        JSON: Success or error message.
    """
    time_entry = TimeEntry.query.get(entry_id)

    if time_entry:
        task = time_entry.task
        if not is_user_authorized_for_task(task, current_user.user_id):
            return jsonify({"error": "You are not authorized to delete this time entry"}), 403

        task_id = time_entry.task_id
        result = delete_time_entry(entry_id)
        update_durations_for_task_and_project(task_id)
        return jsonify(result)
    else:
        result = delete_time_entry(entry_id)
        return jsonify(result)


@time_entry_bp.route("/<int:entry_id>", methods=["PUT"])
@login_required
def update_entry(entry_id):
    """
    Update fields of a time entry.

    JSON Payload: Any subset of:
        - start_time
        - end_time
        - duration_seconds
        - comment

    Returns:
        JSON: Success message or error.
    """
    time_entry = TimeEntry.query.get(entry_id)
    if time_entry:
        task = time_entry.task
        if not is_user_authorized_for_task(task, current_user.user_id):
            return jsonify({"error": "You are not authorized to update this time entry"}), 403

    data = request.get_json()
    result = update_time_entry(entry_id, **data)

    if time_entry and time_entry.task_id:
        update_durations_for_task_and_project(time_entry.task_id)

    return jsonify(result)

"""
I MADE A CHANGE IN HERE, CHECK IF IT'S ALRIGHT(JUDE)>>>>>>

"""
@time_entry_bp.route("/latest_sessions", methods=["GET"])
@login_required
def get_latest_sessions():
    """
    Get the user's most recent time entries (Latest Sessions).
    """
    entries = time_entry_service.get_latest_time_entries_for_user(current_user.user_id)
    return jsonify([entry.to_dict() for entry in entries])


@time_entry_bp.route("/latest_project_entry", methods=["GET"])
@login_required
def latest_project_entry():
    """
    Returns the latest time entry linked to a task that belongs to a project.

    Returns:
        JSON: Includes time_entry, task and project information.
    """
    result = get_latest_project_time_entry_for_user(current_user.user_id)

    if not result:
        return jsonify({"error": "No suitable time entry found"}), 404

    return jsonify({
        "time_entry": result["time_entry"].to_dict(),
        "task": result["task"].to_dict(),
        "project": result["project"].to_dict()
    }), 200