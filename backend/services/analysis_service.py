from collections import defaultdict
from datetime import datetime, timedelta

from flask_login import current_user

from backend.models import TimeEntry, Task, Project


def load_time_entries():
    """
    Load all time entries for the current logged-in user.

    Returns:
        list of dict: List of time entries with keys:
            - 'start' (datetime): Start datetime of the time entry
            - 'end' (datetime): End datetime of the time entry
            - 'task' (str): Task title
            - 'project' (str): Project name (may be None)
    """
    if not current_user.is_authenticated:
        return []
    entries = TimeEntry.query.filter_by(user_id=current_user.user_id).all()
    result = []
    for entry in entries:
        result.append(
            {
                "start": entry.start_time,
                "end": entry.end_time,
                "task": entry.task.title,
                "project": entry.task.project.name if entry.task.project else None,
            }
        )
    return result


def load_tasks():
    """
    Load all tasks for the current logged-in user.

    Returns:
        list of dict: List of tasks with keys:
            - 'project' (str): Project name
            - 'status' (str): Task status, e.g., "done", "open"
            - 'title' (str): Task title
            - 'start_date' (datetime or None): Task start date if available
    """
    if not current_user.is_authenticated:
        return []
    tasks = Task.query.filter_by(user_id=current_user.user_id).all()
    result = []
    for task in tasks:
        result.append(
            {
                "project": task.project.name if task.project else None,
                "status": task.status,
                "title": task.title,
                "due_date": task.due_date if task.due_date else None,
            }
        )
    return result


def load_projects():
    """
    Load all projects for the current logged-in user.

    Returns:
        list of Project: List of Project model instances
    """
    if not current_user.is_authenticated:
        return []
    return Project.query.filter_by(user_id=current_user.user_id).all()


def filter_time_entries_by_date(time_entries, start_date, end_date):
    """
    Filter time entries to those between start_date and end_date inclusive.

    Args:
        time_entries (list of dict): List of time entry dicts with 'start' key.
        start_date (datetime): Start datetime for filtering.
        end_date (datetime): End datetime for filtering.

    Returns:
        list of dict: Filtered time entries.
    """
    filtered = [e for e in time_entries if start_date <= e["start"] <= end_date]
    return filtered


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
        result[proj] = val["done"] / val["total"] if val["total"] > 0 else 0
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
        project = e.get("project") or "No project"
        actual[project] += (e["end"] - e["start"]).total_seconds() / 3600

    comparison = {}
    for project in set(list(actual.keys()) + list(target.keys())):
        key = project or "No project"
        comparison[key] = {
            "actual": actual.get(project, 0) or 0,
            "target": target.get(project, 0) or 0,
        }
    return comparison


def load_target_times():
    """
    Loads the target planned hours per project for the current user.

    Returns:
        dict: Mapping from project name to planned hours (float).
    """
    if not current_user.is_authenticated:
        return {}
    projects = load_projects()
    return {p.name: p.time_limit_hours for p in projects}


def tasks_in_month(tasks, year, month):
    filtered = []
    for t in tasks:
        if (
            "start_date" in t
            and t["start_date"]
            and t["start_date"].year == year
            and t["start_date"].month == month
        ):
            filtered.append(t)
    return filtered


def calendar_due_dates():
    """
    Loads all project and task due dates and formats them as calendar events.

    Returns:
        list: List of event dictionaries containing title, start, end, and color.
    """
    events = []

    # Projekte mit due_date
    projects = Project.query.filter(Project.due_date.isnot(None)).all()
    for p in projects:
        events.append(
            {
                "title": f"Project: {p.name}",
                "start": p.due_date.date().isoformat(),
                "end": p.due_date.date().isoformat(),
                "color": "#EE0000",
            }
        )

    # Tasks mit due_date
    tasks = Task.query.filter(Task.due_date.isnot(None)).all()
    for t in tasks:
        events.append(
            {
                "title": f"Task: {t.title}",
                "start": t.due_date.date().isoformat(),
                "end": t.due_date.date().isoformat(),
                "color": "#b30000",
            }
        )

    return events


def calendar_worked_time():
    """
    Returns one calendar event per task per day with total duration in h:min:s
    """
    time_entries = load_time_entries()
    if not time_entries:
        return []

    grouped = defaultdict(
        lambda: defaultdict(lambda: {"duration": [], "project": None})
    )

    for entry in time_entries:
        date = entry["start"].date().isoformat()
        task = entry["task"]
        duration_sec = (entry["end"] - entry["start"]).total_seconds()
        grouped[date][task]["duration"].append(duration_sec)
        grouped[date][task]["project"] = entry["project"]

    events = []
    for date, tasks in grouped.items():
        for task_name, task_data in tasks.items():
            total = sum(task_data["duration"])
            hours = int(total // 3600)
            minutes = int((total % 3600) // 60)
            seconds = int(total % 60)
            project_name = task_data["project"]

            events.append(
                {
                    "title": f"{task_name}: {hours}h {minutes}min {seconds}s",
                    "start": date,
                    "allDay": True,
                    "color": "#7ab8f5",
                    "extendedProps": {"project": project_name},
                }
            )

    return events


def worked_time_today():
    """
    Calculates the total worked time (in hours) for today.

    Returns:
        float: Total hours worked today.
    """
    time_entries = load_time_entries()
    if not time_entries:
        return 0.0

    today = datetime.today().date()
    total_seconds = 0

    for entry in time_entries:
        if entry["start"].date() == today:
            duration = (entry["end"] - entry["start"]).total_seconds()
            total_seconds += duration

    return round(total_seconds / 3600, 2)


def aggregate_time_by_day_project_task(entries, week_start):
    """
    Gibt ein dict zurück: { (project, task): [Mo–So] }
    """
    result = defaultdict(lambda: [0] * 7)
    for e in entries:
        start = e["start"]
        end = e["end"]
        if not (week_start.date() <= start.date() < (week_start + timedelta(days=7)).date()):
            continue
        day_index = (start.date() - week_start.date()).days
        hours = (end - start).total_seconds() / 3600
        key = (e["project"] or "No Project", e["task"])
        result[key][day_index] += hours
    return result


