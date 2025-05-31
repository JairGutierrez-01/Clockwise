from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from backend.services.analysis_service import calendar_due_dates
from backend.services.analysis_service import (
    aggregate_weekly_time,
    calendar_events,
    progress_per_project,
    actual_target_comparison,
    load_tasks_from_db,
    load_target_times_from_db,
    load_time_entries_from_db,
)

analysis_bp = Blueprint("analysis", __name__)


@analysis_bp.route("/weekly-time")
def weekly_time():
    """
    Endpoint to get aggregated weekly hours worked per project.

    Query Parameters:
        start_date (str): Optional. Start date of the week in 'YYYY-MM-DD' format.
                          Defaults to the current week's Monday.

    Returns:
        JSON: A dictionary where keys are project names and values are lists of 7 floats,
              each representing hours worked per day of the week starting from start_date.
    """
    start_date_str = request.args.get("start_date")
    if start_date_str:
        week_start = datetime.strptime(start_date_str, "%Y-%m-%d")
    else:
        today = datetime.today()
        week_start = today - timedelta(days=today.weekday())

    time_entries = load_time_entries_from_db()

    result = aggregate_weekly_time(time_entries, week_start)
    json_result = {project: hours for project, hours in result.items()}
    return jsonify(json_result)


@analysis_bp.route("/projects")
def projects_events():
    """
    Endpoint to get all time entries as calendar events.

    Returns:
        JSON: A dictionary with key "time_entries" containing a list of event dictionaries.
              Each event has 'title', 'start' (ISO8601 string), and 'end' (ISO8601 string).
    """
    time_entries = load_time_entries_from_db()
    events = calendar_events(time_entries)
    return jsonify({"time_entries": events})


@analysis_bp.route("/progress")
def progress():
    """
    Endpoint to get task progress per project.

    Returns:
        JSON: A dictionary mapping project names to progress ratios (float between 0 and 1).
    """
    tasks = load_tasks_from_db()
    progress_data = progress_per_project(tasks)
    return jsonify(progress_data)


@analysis_bp.route("/actual-target")
def actual_target():
    """
    Endpoint to compare actual worked hours against target hours per project.

    Returns:
        JSON: A dictionary mapping project names to dictionaries containing
              'actual' (float) and 'target' (float) hours.
    """
    time_entries = load_time_entries_from_db()
    target = load_target_times_from_db()

    comparison = actual_target_comparison(time_entries, target)
    return jsonify(comparison)


@analysis_bp.route("/calendar-due-dates")
def get_calendar_due_dates():
    """
    API endpoint that returns all project and task due dates for calendar display.

    Returns:
        Response: JSON list of calendar event dictionaries including title, date, and color.
    """
    events = calendar_due_dates()
    return jsonify(events)
