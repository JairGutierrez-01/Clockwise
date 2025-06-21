from datetime import datetime

from backend.database import db
from backend.models.task import Task
from backend.models.time_entry import TimeEntry
from backend.models.project import Project
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
        dict: Success message or error if task already has an entry.
    """
    # Parse provided date/time strings into datetime objects
    if isinstance(start_time, str):
        try:
            start_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            start_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M")
    if isinstance(end_time, str):
        try:
            end_time = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            end_time = datetime.strptime(end_time, "%Y-%m-%d %H:%M")
    task = Task.query.get(task_id)

    if task.member_id is not None and task.member_id != user_id:
        return {"error": "You are not assigned to this task"}

    if not task:
        return {"error": "Task not found"}

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


def get_time_entry_by_id(time_entry_id):
    """
    Retrieve a time entry by its ID.

    Args:
        time_entry_id (int): Time entry ID.

    Returns:
        TimeEntry or None: The found entry or None.
    """
    return TimeEntry.query.get(time_entry_id)


def get_time_entries_by_task(task_id):
    """
    Retrieve all time entries assigned to a specific task.

    Args:
        task_id (int): ID of the task.

    Returns:
        list[TimeEntry]: All associated time entries.
    """
    return TimeEntry.query.filter_by(task_id=task_id).all()


def update_time_entry(time_entry_id, **kwargs):
    """
    Update fields of a time entry.

    Args:
        time_entry_id (int): The ID of the time entry to update.
        **kwargs: Fields to update (start_time, end_time, duration_seconds, comment).

    Returns:
        dict: Success or error.
    """
    entry = TimeEntry.query.get(time_entry_id)
    if not entry:
        return {"error": "Time entry not found"}

    if "start_time" in kwargs and kwargs["start_time"]:
        kwargs["start_time"] = datetime.strptime(
            kwargs["start_time"], "%Y-%m-%d %H:%M:%S"
        )
    if "end_time" in kwargs and kwargs["end_time"]:
        kwargs["end_time"] = datetime.strptime(kwargs["end_time"], "%Y-%m-%d %H:%M:%S")

    ALLOWED_TIME_ENTRY_FIELDS = [
        "start_time",
        "end_time",
        "duration_seconds",
        "comment",
    ]

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
        dict: Success or error message.
    """
    entry = TimeEntry.query.get(time_entry_id)
    if not entry:
        return {"error": "Time entry not found"}

    task = entry.task  # Task merken, bevor der Entry gelöscht wird

    db.session.delete(entry)
    db.session.commit()

    # Wenn der Task leer und automatisch erstellt wurde → Task auch löschen
    if task and task.created_from_tracking and not task.time_entries:
        db.session.delete(task)
        db.session.commit()

    return {"success": True, "message": "Time entry deleted successfully"}


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
    Pause a time entry by calculating current duration and clearing start_time.

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
    Resume a paused time entry by setting a new start time.

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


def get_tasks_with_time_entries():
    """
    Retrieve all tasks that have at least one time entry.

    Returns:
        list: A list of Task objects with time entries.
    """
    from backend.models.task import Task
    from backend.models.time_entry import TimeEntry

    # Alle gültigen (nicht-null) Task-IDs mit TimeEntries
    task_ids_with_entries = (
        db.session.query(TimeEntry.task_id)
        .filter(TimeEntry.task_id != None)
        .distinct()
        .all()
    )

    task_ids = [tid[0] for tid in task_ids_with_entries if tid[0] is not None]

    if not task_ids:
        return []

    return Task.query.filter(Task.task_id.in_(task_ids)).all()


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


# New function from JUDE
def get_latest_time_entries_for_user(user_id, limit=10):
    """
    Retrieve the most recent completed time entries for a given user.

    Args:
        user_id (int): ID of the user.
        limit (int): Maximum number of entries to return.

    Returns:
        list[TimeEntry]: List of TimeEntry objects ordered by start_time descending.
    """
    return (
        TimeEntry.query
        .filter_by(user_id=user_id)
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
        dict | None: Dictionary with time_entry, task and project, or None if not found.
    """

    # Find latest time entry where its task has a project_id
    entry = (
        TimeEntry.query
        .join(TimeEntry.task)
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
        "project": project
    }
