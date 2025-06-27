from datetime import datetime

from backend.database import db
from backend.models.task import Task
from backend.models.time_entry import TimeEntry
from backend.services.project_service import update_total_duration_for_project
from backend.services.task_service import update_total_duration_for_task


def create_time_entry(
    user_id,
    task_id,
    start_time=None,
    end_time=None,
    duration_seconds=None,
    comment=None,
):
    """
    Create a new time entry for a task.

    Args:
        user_id (int): ID of the user creating the entry.
        task_id (int): ID of the task associated with the time entry.
        start_time (datetime, optional): Start time of the entry.
        end_time (datetime, optional): End time of the entry.
        duration_seconds (int, optional): Total duration in seconds.
        comment (str, optional): Optional comment.

    Returns:
        dict: Success message or error.
    """

    if start_time:
        start_time = parse_datetime_flexibly(start_time)
    if end_time:
        end_time = parse_datetime_flexibly(end_time)

    task = Task.query.get(task_id)
    if not task:
        return {"error": "Task not found"}

    if task.member_id is not None and task.member_id != user_id:
        return {"error": "You are not assigned to this task"}

    new_entry = TimeEntry(
        user_id=user_id,
        task_id=task_id,
        start_time=start_time or datetime.now(),
        end_time=end_time,
        duration_seconds=duration_seconds,
        comment=comment,
    )

    db.session.add(new_entry)
    db.session.commit()

    return {
        "success": True,
        "message": "Time entry created successfully",
        "time_entry_id": new_entry.time_entry_id,
    }


def update_time_entry(time_entry_id, **kwargs):
    """
    Update a time entry with provided fields.

    Args:
        time_entry_id (int): The ID of the time entry to update.
        **kwargs: Fields to update (e.g., start_time, end_time, duration_seconds, comment).

    Returns:
        dict: Success message or error.
    """
    entry = TimeEntry.query.get(time_entry_id)
    if not entry:
        return {"error": "Time entry not found"}

    if "start_time" in kwargs and kwargs["start_time"]:
        kwargs["start_time"] = parse_datetime_flexibly(kwargs["start_time"])
    if "end_time" in kwargs and kwargs["end_time"]:
        kwargs["end_time"] = parse_datetime_flexibly(kwargs["end_time"])

    ALLOWED_TIME_ENTRY_FIELDS = ["start_time", "end_time", "duration_seconds", "comment"]
    for key, value in kwargs.items():
        if key in ALLOWED_TIME_ENTRY_FIELDS:
            setattr(entry, key, value)

    db.session.commit()

    return {
        "success": True,
        "message": "Time entry updated successfully",
        "time_entry_id": time_entry_id,
    }


def delete_time_entry(time_entry_id):
    """
    Delete a time entry by its ID.

    Args:
        time_entry_id (int): ID of the time entry to delete.

    Returns:
        dict: Success message or error.
    """
    entry = TimeEntry.query.get(time_entry_id)
    if not entry:
        return {"error": "Time entry not found"}

    related_task = entry.task

    db.session.delete(entry)
    db.session.commit()

    if related_task and related_task.created_from_tracking and not related_task.time_entries:
        db.session.delete(related_task)
        db.session.commit()

    return {
        "success": True,
        "message": "Time entry deleted successfully"}


def get_time_entry_by_id(time_entry_id):
    """
    Retrieve a time entry by its ID.

    Args:
        time_entry_id (int): ID of the Time entry.

    Returns:
        TimeEntry or None: The corresponding entry or None.
    """
    return TimeEntry.query.get(time_entry_id)


def get_time_entries_by_task(task_id):
    """
    Retrieve all time entries assigned to a specific task.

    Args:
        task_id (int): ID of the task.

    Returns:
        list[TimeEntry]: List of all associated time entries.
    """
    return TimeEntry.query.filter_by(task_id=task_id).all()


def get_latest_time_entries_for_user(user_id, limit=10):
    """
    Retrieve the latest completed time entries for a given user.

    Args:
        user_id (int): ID of the user.
        limit (int): Maximum number of entries to return.

    Returns:
        list[TimeEntry]: Sorted list of finished time entries sorted by start time descending.
    """
    return (
        TimeEntry.query.filter_by(user_id=user_id)
        .filter(TimeEntry.end_time.isnot(None))
        .order_by(TimeEntry.start_time.desc())
        .limit(limit)
        .all()
    )


def get_latest_project_time_entry_for_user(user_id):
    """
    Get the latest time entry for the user where the associated task is linked to a project.

    Args:
        user_id (int): The user's ID.

    Returns:
        dict or None: Dictionary containing time_entry, task, and project, or None if not found.
    """

    entry = (
        TimeEntry.query.join(TimeEntry.task)
        .filter(TimeEntry.user_id == user_id)
        .filter(TimeEntry.end_time.isnot(None))
        .filter(Task.project_id.isnot(None))
        .order_by(TimeEntry.start_time.desc())
        .first()
    )

    if not entry:
        return None

    task = entry.task
    project = task.project if task else None

    return {
        "time_entry": entry,
        "task": task,
        "project": project,
    }


def start_time_entry(user_id, task_id, comment=None):
    """
    Start a time entry for a task, marking the current time as start.

    Args:
        user_id (int): The user starting the time entry.
        task_id (int): The task to track time for.
        comment (str, optional): Optional note.

    Returns:
        dict: Success message or error.
    """
    task = Task.query.get(task_id)
    if not task:
        return {"error": "Task not found"}

    # Check if there is already an active time entry for this task/user
    active_entry = TimeEntry.query.filter_by(
        task_id=task_id, user_id=user_id, end_time=None
    ).first()
    if active_entry:
        return {"error": "There is already an active time entry for this task"}

    new_entry = TimeEntry(
        user_id=user_id,
        task_id=task_id,
        start_time=datetime.now(),
        comment=comment,
    )
    db.session.add(new_entry)
    db.session.commit()

    return {
        "success": True,
        "message": "Time tracking started successfully",
        "time_entry_id": new_entry.time_entry_id,
    }


def stop_time_entry(time_entry_id):
    """
    Stop an active time entry and calculate its duration.

    Args:
        time_entry_id (int): ID of the entry to stop.

    Returns:
        dict: Success message with duration or error.
    """
    entry = TimeEntry.query.get(time_entry_id)
    if not entry:
        return {"error": "Time entry not found"}
    if entry.end_time:
        return {"error": "Time entry is already ended"}

    entry.end_time = datetime.now()

    if entry.start_time:
        current_duration = int((entry.end_time - entry.start_time).total_seconds())
        entry.duration_seconds = (entry.duration_seconds or 0) + current_duration

    db.session.commit()

    return {
        "success": True,
        "message": "Time tracking stopped successfully",
        "duration_seconds": entry.duration_seconds,
    }


def pause_time_entry(time_entry_id):
    """
    Pause a time entry by calculating current duration and clearing start_time to indicate it is paused.

    Args:
        time_entry_id (int): ID of the time entry to pause.

    Returns:
        dict: Success message or error.
    """
    entry = TimeEntry.query.get(time_entry_id)
    if not entry:
        return {"error": "Time entry not found"}
    if entry.end_time:
        return {"error": "Time entry has already stopped"}
    if entry.start_time is None:
        return {"error": "Time entry is already paused"}

    now = datetime.now()
    current_duration = int((now - entry.start_time).total_seconds())
    entry.duration_seconds = (entry.duration_seconds or 0) + current_duration
    entry.start_time = None

    db.session.commit()

    return {
        "success": True,
        "message": "Time tracking paused successfully",
        "duration_seconds": entry.duration_seconds,
    }


def resume_time_entry(time_entry_id):
    """
    Resume a paused time entry by setting a new start_time.

    Args:
        time_entry_id (int): ID of the paused time entry.

    Returns:
        dict: Success message or error if the entry is not found or already running.
    """
    entry = TimeEntry.query.get(time_entry_id)
    if not entry:
        return {"error": "Time entry not found"}
    if entry.start_time:
        return {"error": "Time entry is already running"}

    entry.start_time = datetime.now()

    db.session.commit()

    return {
        "success": True,
        "message": "Time tracking resumed successfully",
        "start_time": entry.start_time,
    }


def update_durations_for_task_and_project(task_id):
    """
    Recalculate and update the duration values for a task and its associated project (if any).

    Args:
        task_id (int): ID of the task whose durations should be updated.
    """
    task_result = update_total_duration_for_task(task_id)

    if task_result.get("success"):
        task = Task.query.get(task_id)
        if task and task.project_id:
            update_total_duration_for_project(task.project_id)

    return task_result


def parse_datetime_flexibly(value):
    """
    Attempt to parse a datetime value in flexible formats.

    Args:
        value (str or datetime): The datetime to parse.

    Returns:
        datetime or ValueError: Parsed datetime object or error, if no matching format is found.
    """
    if not isinstance(value, str):
        return value

    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%d.%m.%Y %H:%M:%S",
        "%d.%m.%Y %H:%M",
    ):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue

    raise ValueError(f"Invalid datetime format: {value}")


