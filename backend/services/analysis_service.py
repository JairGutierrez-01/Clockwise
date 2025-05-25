from collections import defaultdict
from datetime import datetime, timedelta
from flask_login import current_user

from backend.models import TimeEntry, Task, Project


def aggregate_weekly_time(time_entries, week_start_date):
    """
    Aggregate worked hours per project for each day of the given week.

    Args:
        time_entries (list of dict): List of time entry dictionaries with keys:
            - 'start' (datetime): Start datetime of the time entry
            - 'end' (datetime): End datetime of the time entry
            - 'project' (str): Project name
        week_start_date (datetime): The start date of the week (e.g., Monday)

    Returns:
        defaultdict: Dictionary mapping project names to a list of 7 floats,
                     each representing total hours worked on each day of the week
                     starting from `week_start_date`.
    """
    project_hours = defaultdict(lambda: [0] * 7)
    for entry in time_entries:
        start = entry["start"]
        end = entry["end"]
        project = entry["project"]
        if (
            week_start_date.date()
            <= start.date()
            < (week_start_date + timedelta(days=7)).date()
        ):
            day_idx = (start.date() - week_start_date.date()).days
            hours = (end - start).total_seconds() / 3600
            project_hours[project][day_idx] += hours
    return project_hours


def calendar_events(time_entries):
    """
    Convert time entries to calendar event format for frontend calendar rendering.

    Args:
        time_entries (list of dict): List of time entry dictionaries with keys:
            - 'start' (datetime): Start datetime of the time entry
            - 'end' (datetime): End datetime of the time entry
            - 'project' (str): Project name

    Returns:
        list of dict: List of event dictionaries with keys:
            - 'title' (str): Event title (project name)
            - 'start' (str): ISO8601 formatted start datetime
            - 'end' (str): ISO8601 formatted end datetime
    """
    events = []
    for e in time_entries:
        events.append(
            {
                "title": e["project"],
                "start": e["start"].isoformat(),
                "end": e["end"].isoformat(),
            }
        )
    return events


def progress_per_project(tasks):
    """
    Calculate progress per project as the ratio of completed tasks.

    Args:
        tasks (list of dict): List of task dictionaries with keys:
            - 'project' (str): Project name
            - 'status' (str): Task status, e.g., "done" or "open"

    Returns:
        dict: Dictionary mapping project names to progress ratio (float between 0 and 1).
    """
    progress = defaultdict(lambda: {"done": 0, "total": 0})
    for t in tasks:
        progress[t["project"]]["total"] += 1
        if t["status"] == "done":
            progress[t["project"]]["done"] += 1

    result = {}
    for proj, val in progress.items():
        if val["total"] > 0:
            result[proj] = val["done"] / val["total"]
        else:
            result[proj] = 0
    return result


def actual_target_comparison(time_entries, target):
    """
    Compare actual worked hours against target hours per project.

    Args:
        time_entries (list of dict): List of time entry dictionaries with keys:
            - 'start' (datetime): Start datetime of the time entry
            - 'end' (datetime): End datetime of the time entry
            - 'project' (str): Project name
        target (dict): Dictionary mapping project names to target hours (float)

    Returns:
        dict: Dictionary mapping project names to dict with:
            - 'actual' (float): Total worked hours
            - 'target' (float): Target hours
    """
    actual = defaultdict(float)
    for e in time_entries:
        actual[e["project"]] += (e["end"] - e["start"]).total_seconds() / 3600

    comparison = {}
    for project in set(list(actual.keys()) + list(target.keys())):
        comparison[project] = {
            "actual": actual.get(project, 0),
            "target": target.get(project, 0),
        }
    return comparison


def load_time_entries_from_db():
    """
    Loads all time entries for the currently logged-in user from the database.

    Returns:
        list of dict: List of time entries with keys 'start', 'end', and 'project'.
    """
    if not current_user.is_authenticated:
        return []

    time_entries = TimeEntry.query.filter_by(user_id=current_user.user_id).all()
    result = []
    for entry in time_entries:
        result.append(
            {
                "start": entry.start_time,
                "end": entry.end_time,
                "project": entry.task.title,
            }
        )
    return result


def load_tasks_from_db():
    """
    Loads all tasks belonging to the currently logged-in user from the database.

    Returns:
        list of dict: List of tasks with keys 'project' and 'status'.
    """
    if not current_user.is_authenticated:
        return []

    tasks = Task.query.filter_by(user_id=current_user.user_id).all()

    result = []
    for task in tasks:
        result.append(
            {
                "project": task.project_id.name,
                "status": task.status,
            }
        )
    return result


def load_target_times_from_db():
    """
    Loads the target planned hours per project for the current user.

    Returns:
        dict: Mapping from project name to planned hours (float).
    """
    if not current_user.is_authenticated:
        return {}

    projects = Project.query.filter_by(user_id=current_user.id).all()

    result = {}
    for project in projects:
        result[project.project] = project.time_limit_hours
    return result
