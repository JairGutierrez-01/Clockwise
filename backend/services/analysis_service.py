import csv
from collections import defaultdict
from datetime import datetime, timedelta
from io import StringIO, BytesIO

from flask_login import current_user
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from sqlalchemy import or_

from backend.database import db
from backend.models import TimeEntry, Task, Project, Notification
from backend.services.notification_service import (
    notify_weekly_goal_achieved,
    already_notified_this_week,
)


def export_time_entries_pdf(time_entries):
    """
    Export time entries as PDF Bytes.

    Args:
        time_entries (list of dict): Time entries with the keys 'start', 'end', 'task', 'project'

    Returns:
        bytes: PDF data
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    c.setFont("Helvetica", 12)
    y = height - 40
    line_height = 18

    # Header
    c.drawString(30, y, "Start")
    c.drawString(150, y, "End")
    c.drawString(270, y, "Task")
    c.drawString(400, y, "Project")
    y -= line_height

    for entry in time_entries:
        if y < 40:  # New Site if full
            c.showPage()
            c.setFont("Helvetica", 12)
            y = height - 40
        c.drawString(30, y, entry["start"].strftime("%Y-%m-%d %H:%M"))
        c.drawString(150, y, entry["end"].strftime("%Y-%m-%d %H:%M"))
        c.drawString(270, y, entry["task"][:25])  # Max. 25 Zeichen
        c.drawString(400, y, entry["project"] or "")
        y -= line_height

    c.save()
    pdf = buffer.getvalue()
    buffer.close()
    return pdf


def export_time_entries_csv(time_entries):
    """
    Export time entries as CSV string.

    Args:
        time_entries (list of dict): Time entries with keys 'start', 'end', 'task', 'project'

    Returns:
        str: CSV formated text
    """
    output = StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow(["Start", "End", "Task", "Project"])

    # Rows
    for entry in time_entries:
        writer.writerow(
            [
                entry["start"].isoformat(),
                entry["end"].isoformat(),
                entry["task"],
                entry["project"] or "",
            ]
        )

    return output.getvalue()


def load_time_entries():
    """
    Load all time entries for the current logged-in user.

    Returns:
        list of dict: List of time entries with keys:
            - 'start' (datetime): Start datetime of the time entry
            - 'end' (datetime): End datetime of the time entry
            - 'task' (str): Task title
            - 'project' (str): Project name (maybe None)
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
    Load all tasks visible to the current user:
      - Solo tasks (user_id)
      - Tasks assigned to them in team projects (member_id)
      - All tasks in team projects they administer (admin_id)

    Returns:
        list of dict: List of tasks with keys:
            - 'project' (str): Project name
            - 'status' (str): Task status ("todo", "in_progress", "done")
            - 'title' (str): Task title
            - 'due_date' (datetime or None): Task due date if available
    """
    if not current_user.is_authenticated:
        return []

    # Show solo, assigned, and admin‐created tasks
    tasks = Task.query.filter(
        or_(
            Task.user_id == current_user.user_id,
            Task.member_id == current_user.user_id,
            Task.admin_id == current_user.user_id,
        )
    ).all()

    result = []
    for task in tasks:
        result.append(
            {
                "project": task.project.name if task.project else None,
                "project_status": (
                    task.project.status.value
                    if task.project and task.project.status
                    else None
                ),
                "status": task.status.value,
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
        time_entries (list of dict): List of time entry dicts with the 'start' key.
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
        default dict: Dictionary mapping project names to a list of 7 floats,
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
        project_name = t.get("project")
        if not project_name:
            continue  # Skip tasks with no project name
        progress[project_name]["total"] += 1
        if t["status"] == "done":
            progress[project_name]["done"] += 1

    result = {}
    for proj, val in progress.items():
        result[proj] = val["done"] / val["total"] if val["total"] > 0 else 0
    return result


def actual_target_comparison(time_entries, target, notify=False, user_id=None):
    """
    Compare actual worked hours against target hours per project and optionally notify when goal is reached.

    Args:
        time_entries (list of dict): List of time entry dictionaries with keys:
            - 'start' (datetime)
            - 'end' (datetime)
            - 'project' (str)
        target (dict): Project name → target hours
        notify (bool): If True, trigger notification when target is reached
        user_id (int or None): Required if notify=True

    Returns:
        dict: Project name → { 'actual': float, 'target': float }
    """
    actual = defaultdict(float)
    for e in time_entries:
        project = e.get("project") or "No project"
        actual[project] += (e["end"] - e["start"]).total_seconds() / 3600

    comparison = {}
    for project in set(actual.keys()).union(target.keys()):
        actual_hours = actual.get(project, 0)
        target_hours = target.get(project, 0)
        comparison[project] = {
            "actual": actual_hours,
            "target": target_hours,
        }

        if notify and user_id and actual_hours >= target_hours > 0:
            notify_weekly_goal_achieved(user_id, project)

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
    """
    Filters a list of tasks to include only those that start in the specified month and year.

    Args:
        tasks (list): A list of task dictionaries. Each dictionary should contain a 'start_date' key with a datetime value.
        year (int): The year to filter tasks by.
        month (int): The month to filter tasks by (1–12).

    Returns:
        list: A list of task dictionaries that start in the specified year and month.
    """
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
    Generates one calendar event per task per day with the total worked duration in hours, minutes, and seconds.

    Returns:
        list: A list of calendar event dictionaries. Each dictionary includes:
            - 'title' (str): The task name and duration formatted as "Task: Xh Ymin Zs".
            - 'start' (str): The date of the entry in ISO format (YYYY-MM-DD).
            - 'allDay' (bool): Always True, indicating an all-day event.
            - 'color' (str): A fixed color hex code for styling the event.
            - 'extendedProps' (dict): Additional data, such as the project name.
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


def aggregate_time_by_day_project_task(entries, week_start):
    """
    Aggregates time entries by (project, task) and weekday within a given week.

    Args:
        entries (list): A list of time entry dictionaries. Each must include 'start', 'end', 'project', and 'task'.
        week_start (datetime): The starting date (Monday) of the week to aggregate.

    Returns:
        dict: A dictionary with (project, task) tuples as keys, and a list of 7 float values as values.
              Each value in the list represents the number of hours worked on that (project, task) per weekday (Monday=0, Sunday=6).
    """
    result = defaultdict(lambda: [0] * 7)
    for e in entries:
        start = e["start"]
        end = e["end"]
        if not (
            week_start.date() <= start.date() < (week_start + timedelta(days=7)).date()
        ):
            continue
        day_index = (start.date() - week_start.date()).days
        hours = (end - start).total_seconds() / 3600
        key = (e["project"] or "No Project", e["task"])
        result[key][day_index] += hours
    return result


def overall_progress(tasks):
    """
    Calculates the overall progress across all active projects based on completed tasks.

    Args:
        tasks (list): A list of task dictionaries. Each must include at least 'project', 'status',
                      and 'project_status' to determine if the associated project is active.

    Returns:
        float: A value between 0 and 1 representing the ratio of completed tasks
               to total tasks in active projects. Returns 0 if no relevant tasks exist.
    """
    done = 0
    total = 0
    for t in tasks:
        if not t.get("project") or t.get("project_status") != "active":
            continue
        total += 1
        if t["status"] == "done":
            done += 1
    return done / total if total > 0 else 0


def notify_weekly_status(user_id, current_date=None):
    """
    Send weekly notifications per project about worked hours vs planned hours.

    Args:
        user_id (int): Nutzer-ID
        current_date (datetime, optional): Referenzdatum (Standard: heute)
    """
    if current_date is None:
        current_date = datetime.now()

    projects = load_projects()  # Projekt-Objekte laden
    time_entries = load_time_entries()  # Alle Zeiteinträge laden (ggf. nur für user_id)

    for project in projects:
        if not (project.created_at and project.due_date and project.time_limit_hours):
            continue  # Daten unvollständig

        # Wochenanzahl zwischen Start und Ende
        total_days = (project.due_date - project.created_at).days
        total_weeks = max(total_days / 7, 1)  # mindestens 1 Woche

        # Erwartete Stunden pro Woche
        planned_hours_per_week = project.time_limit_hours / total_weeks

        # Wie viele Wochen sind seit Projektstart bis jetzt vergangen?
        weeks_passed = (current_date - project.created_at).days / 7
        weeks_passed = min(max(weeks_passed, 0), total_weeks)

        # Erwartete kumulierte Stunden bis jetzt
        expected_cumulative_hours = planned_hours_per_week * weeks_passed

        # Tatsächliche kumulierte Stunden bis jetzt (für dieses Projekt)
        actual_cumulative_hours = 0
        for entry in time_entries:
            if entry["project"] == project.name and entry["end"] <= current_date:
                duration = (entry["end"] - entry["start"]).total_seconds() / 3600
                actual_cumulative_hours += duration

        # Stunden in der aktuellen Woche ermitteln
        # Annahme: Woche startet Montag
        current_week_start = current_date - timedelta(days=current_date.weekday())
        current_week_end = current_week_start + timedelta(days=7)
        actual_this_week = 0
        for entry in time_entries:
            if (
                entry["project"] == project.name
                and current_week_start <= entry["start"] < current_week_end
            ):
                duration = (entry["end"] - entry["start"]).total_seconds() / 3600
                actual_this_week += duration

        # Status bestimmen
        deviation = actual_cumulative_hours - expected_cumulative_hours
        status = "in the should"
        if deviation < -planned_hours_per_week * 0.1:  # >10% weniger als geplant
            status = "behind plan"
        elif deviation > planned_hours_per_week * 0.1:
            status = "in advance"

        # Nachricht bauen
        message = (
            f"Project '{project.name}': This week you worked {actual_this_week:.1f}h.\n"
            f"Until now {expected_cumulative_hours:.1f}h were expected.\n"
            f"You are {status} (Deviation {deviation:.1f}h)."
        )

        if not already_notified_this_week(user_id, project.project_id):
            # Notification anlegen und abspeichern
            notification = Notification(
                user_id=user_id,
                project_id=project.project_id,
                message=message,
                type="progress",
                created_at=current_date,
            )
            db.session.add(notification)
            db.session.commit()

            print(f"Weekly status notification for project '{project.name}' sent.")
