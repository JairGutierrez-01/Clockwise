from datetime import datetime

from flask import Blueprint, request, jsonify
from flask_login import login_required
from datetime import datetime, timedelta
from backend.services.analysis_service import aggregate_weekly_time
from backend.services.analysis_service import aggregate_time_by_day_project_task


from backend.services.analysis_service import (
    load_time_entries,
    load_target_times,
    load_tasks,
    tasks_in_month,
    filter_time_entries_by_date,
    worked_time_today,
)
from backend.services.analysis_service import (
    progress_per_project,
    actual_target_comparison,
)

analysis_bp = Blueprint("analysis", __name__, url_prefix="/api/analysis")


# For Testing: /time-entries?start_date=2025-06-01&end_date=2025-06-07
@analysis_bp.route("/time-entries")
@login_required
def api_time_entries():
    """
    Get time entries filtered by a date range.

    Query Parameters:
        start_date (str): Start date in ISO8601 format (YYYY-MM-DDTHH:MM:SS).
        end_date (str): End date in ISO8601 format (YYYY-MM-DDTHH:MM:SS).

    Returns:
        JSON response containing a list of time entries with keys:
            - task (str): Task title.
            - start (str): ISO8601 formatted start datetime.
            - end (str): ISO8601 formatted end datetime.
            - duration_hours (float): Duration of the time entry in hours.

    Errors:
        400 if parameters are missing or date formats are invalid.
    """
    start_str = request.args.get("start_date")
    end_str = request.args.get("end_date")
    if not start_str or not end_str:
        return jsonify({"error": "start_date and end_date required"}), 400
    try:
        start_date = datetime.fromisoformat(start_str)
        end_date = datetime.fromisoformat(end_str)
    except ValueError:
        return jsonify({"error": "Invalid date format"}), 400

    entries = load_time_entries()
    filtered = filter_time_entries_by_date(entries, start_date, end_date)
    result = [
        {
            "task": e["task"],
            "start": e["start"].isoformat(),
            "end": e["end"].isoformat(),
            "duration_hours": (e["end"] - e["start"]).total_seconds() / 3600,
        }
        for e in filtered
    ]
    return jsonify(result)


# For Testing: /tasks-in-month?month=2025-05
@analysis_bp.route("/tasks-in-month")
@login_required
def api_tasks_in_month():
    """
    Get all tasks for a specific month.

    Query Parameters:
        month (str): Month in format "YYYY-MM".

    Returns:
        JSON response containing a list of task names with project prefix.

    Errors:
        400 if the month parameter is missing or formatted incorrectly.
    """
    month_str = request.args.get("month")  # Format: "YYYY-MM"
    if not month_str:
        return jsonify({"error": "month parameter required"}), 400
    try:
        year, month = map(int, month_str.split("-"))
    except Exception:
        return jsonify({"error": "Invalid month format"}), 400

    tasks = load_tasks()
    filtered_tasks = tasks_in_month(tasks, year, month)
    task_names = list(
        {t["project"] + ": " + t.get("title", "Unknown Task") for t in filtered_tasks}
    )
    return jsonify(task_names)


@analysis_bp.route("/project-progress")
@login_required
def api_project_progress():
    """
    Get progress ratio per project based on completed tasks.

    Returns:
        JSON response mapping project names to progress ratios (float between 0 and 1).
    """
    tasks = load_tasks()
    progress = progress_per_project(tasks)
    return jsonify(progress)


@analysis_bp.route("/actual-vs-planned")
@login_required
def api_actual_vs_planned():
    """
    Compare actual worked hours against planned target hours per project.

    Returns:
        JSON response mapping project names to dictionaries containing:
            - actual (float): Actual worked hours.
            - target (float): Planned target hours.
    """
    time_entries = load_time_entries()
    targets = load_target_times()
    comparison = actual_target_comparison(time_entries, targets)
    return jsonify(comparison)


@analysis_bp.route("/worked_time_today", methods=["GET"])
@login_required
def get_worked_time_today():
    """
    API endpoint that returns the total worked time for today.

    Returns:
        JSON response with total hours worked today.
    """
    hours_today = worked_time_today()
    return jsonify({"worked_hours_today": hours_today})


@analysis_bp.route("/weekly-time")
@login_required
def api_weekly_time():
    """
    API endpoint that returns the aggregated worked time per project for the current week (Monday to Sunday).

    Returns:
        JSON response with:
            - labels (list of str): Weekday labels ["Mo", "Di", ..., "So"].
            - projects (dict): Mapping of project names to a list of 7 floats,
                               each representing the total hours worked on that day.
    """
    today = datetime.today()
    monday = today - timedelta(days=today.weekday())
    entries = load_time_entries()
    aggregated = aggregate_weekly_time(entries, monday)

    return jsonify(
        {"labels": ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"], "projects": aggregated}
    )


@analysis_bp.route("/weekly-time-stacked")
@login_required
def api_weekly_time_stacked():
    start_param = request.args.get("start")
    if start_param:
        try:
            monday = datetime.fromisoformat(start_param)
        except ValueError:
            return jsonify({"error": "Invalid start date format"}), 400
    else:
        today = datetime.today()
        monday = today - timedelta(days=today.weekday())

    entries = load_time_entries()
    grouped = aggregate_time_by_day_project_task(entries, monday)

    datasets = []
    for (project, task), data in grouped.items():
        datasets.append({"label": f"{project}: {task}", "data": data, "stack": project})

    return jsonify(
        {"labels": ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"], "datasets": datasets}
    )
