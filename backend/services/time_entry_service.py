from backend.database import db
from backend.models.time_entry import TimeEntry
from backend.models.task import Task
from datetime import datetime


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
    task = Task.query.get(task_id)
    if not task:
        return {"error": "Task not found"}
    if task.time_entry:
        return {"error": "Time entry for this task already exists"}

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


def get_time_entry_by_task(task_id):
    """
    Retrieve all time entries assigned to a specific task.

    Args:
        task_id (int): ID of the task.

    Returns:
        list of TimeEntry: All associated time entries.
    """
    return TimeEntry.query.filter_by(task_id=task_id).all()


def update_time_entry(time_entry_id, **kwargs):
    """
    Update fields of a time entry.

    Args:
        time_entry_id (int): The ID of the time entry to update.
        **kwargs: Fields to update.

    Returns:
        dict: Success or error.
    """
    entry = TimeEntry.query.get(time_entry_id)
    if not entry:
        return {"error": "Time entry not found"}

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

    return {
        "success": True,
        "message": "Time entry deleted successfully"
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
    if task.time_entries:
        return {"error": "Time entry for this task already exists"}

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
