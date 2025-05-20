from flask import Blueprint, render_template, request, redirect, url_for
from backend.services.time_entry_service import (
    create_time_entry,
    get_time_entry_by_id,
    get_time_entry_by_task,
    update_time_entry,
    delete_time_entry,
    start_time_entry,
    stop_time_entry,
    pause_time_entry,
    resume_time_entry,
)
from backend.services.task_service import get_default_tasks, get_task_by_id, create_task

time_entry_bp = Blueprint("time_entries", __name__)


@time_entry_bp.route("/time-tracking", methods=["GET"])
def time_tracking_list():
    """
    Display the time tracking page.

    Returns:
        Response: Rendered HTML page for time tracking.
    """
    tasks = get_default_tasks()
    return render_template("timeTracking.html", tasks=tasks)


@time_entry_bp.route("/time-tracking/create", methods=["POST"])
def time_entry_create():
    """
    Handle manual creation of a time entry.

    Returns:
        Response: Redirect to time tracking page after creation.
    """
    user_id = int(request.form.get("user_id"))
    task_id = int(request.form.get("task_id"))
    start_time = request.form.get("start_time")
    end_time = request.form.get("end_time")
    duration = request.form.get("duration")
    comment = request.form.get("comment")

    create_time_entry(
        task_id=task_id,
        user_id=user_id,
        start_time=start_time,
        end_time=end_time,
        duration_minutes=duration,
        comment=comment,
    )
    return redirect(url_for("time_entries.time_tracking_list"))


@time_entry_bp.route(
    "/time-tracking/update/<int:time_entry_id>", methods=["GET", "POST"]
)
def time_entry_update(time_entry_id):
    """
    Edit an existing time entry.

    Args:
        time_entry_id (int): ID of the time entry to update.

    Returns:
        Response: Render update form on GET, perform update on POST.
    """
    entry = get_time_entry_by_id(time_entry_id)
    if not entry:
        return "Time entry not found", 404

    if request.method == "POST":
        start_time = request.form.get("start_time")
        end_time = request.form.get("end_time")
        duration_minutes = request.form.get("duration_minutes")
        comment = request.form.get("comment")

        update_time_entry(
            time_entry_id=time_entry_id,
            start_time=start_time,
            end_time=end_time,
            duration_minutes=duration_minutes,
            comment=comment,
        )
        return redirect(url_for("time_entries.time_tracking_list"))
    return render_template("time_entry_form.html", entry=entry)


@time_entry_bp.route("/time-tracking/start", methods=["POST"])
def time_entry_start():
    """
    Start a time entry for a given task or create an untitled task if none is provided.

    Returns:
        Response: Redirect to time tracking page after starting.
    """
    user_id = int(request.form.get("user_id"))
    task_id = request.form.get("task_id")
    comment = request.form.get("comment")

    if task_id:
        task = get_task_by_id(int(task_id))
        if not task:
            return "Task not found", 404
    else:
        task = create_task(title="Untitled Task", user_id=user_id)

    start_time_entry(user_id=user_id, task_id=task.task_id, comment=comment)
    return redirect(url_for("time_entries.time_tracking_list"))


@time_entry_bp.route("/time-tracking/stop/<int:time_entry_id>", methods=["POST"])
def time_entry_stop(time_entry_id):
    """
    Stop a running time entry and calculate duration.

    Args:
        time_entry_id (int): ID of the time entry to stop.

    Returns:
        Response: Redirect to time tracking page after stopping.
    """
    stop_time_entry(time_entry_id)
    return redirect(url_for("time_entries.time_tracking_list"))


@time_entry_bp.route("/time-tracking/pause/<int:time_entry_id>", methods=["POST"])
def time_entry_pause(time_entry_id):
    """
    Pause a running time entry.

    Args:
        time_entry_id (int): ID of the time entry to pause.

    Returns:
        Response: Redirect to time tracking page after pausing.
    """
    pause_time_entry(time_entry_id)
    return redirect(url_for("time_entries.time_tracking_list"))


@time_entry_bp.route("/time-tracking/resume/<int:time_entry_id>", methods=["POST"])
def time_entry_resume(time_entry_id):
    """
    Resume a paused time entry.

    Args:
        time_entry_id (int): ID of the time entry to resume.

    Returns:
        Response: Redirect to time tracking page after resuming.
    """
    resume_time_entry(time_entry_id)
    return redirect(url_for("time_entries.time_tracking_list"))


@time_entry_bp.route("/time-tracking/delete/<int:time_entry_id>", methods=["POST"])
def time_entry_delete(time_entry_id):
    """
    Delete a time entry.

    Args:
        time_entry_id (int): ID of the time entry to delete.

    Returns:
        Response: Redirect to time tracking page after deletion.
    """
    delete_time_entry(time_entry_id)
    return redirect(url_for("time_entries.time_tracking_list"))


@time_entry_bp.route("/time-tracking/task/<int:task_id>", methods=["GET"])
def time_entry_by_task(task_id):
    """
    Display the time entry for a specific task, if it exists.

    Args:
        task_id (int): ID of the task.

    Returns:
        Response: Rendered HTML page showing the time entry.
    """
    entry = get_time_entry_by_task(task_id)
    return render_template("time_entry_detail.html", entry=entry, task_id=task_id)
