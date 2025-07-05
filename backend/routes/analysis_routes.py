from datetime import datetime, timedelta
from io import BytesIO

from flask import Blueprint, request, jsonify, make_response, send_file
from flask_login import login_required, current_user

from backend.services.analysis_service import (
    aggregate_time_by_day_project_task,
    calculate_expected_progress,
    check_progress_deviation,
)
from backend.services.analysis_service import (
    export_time_entries_pdf,
    export_time_entries_csv,
)
from backend.services.analysis_service import (
    load_time_entries,
    load_target_times,
    load_tasks,
    filter_time_entries_by_date,
)
from backend.services.analysis_service import (
    progress_per_project,
    actual_target_comparison,
)

analysis_bp = Blueprint("analysis", __name__, url_prefix="/api/analysis")


@analysis_bp.route("/project-progress")
@login_required
def api_project_progress():
    """
    Get the progress ratio per project based on completed tasks.

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
    comparison = actual_target_comparison(
        time_entries, targets, notify=True, user_id=current_user.user_id
    )
    return jsonify(comparison)


@analysis_bp.route("/weekly-time-stacked")
@login_required
def api_weekly_time_stacked():
    """
    Retrieves weekly time entries grouped by project and task, stacked per day.

    Query Parameters:
        start (str, optional): Start date (Monday) in ISO format.

    Returns:
        Response: JSON object with:
            - labels (list): Weekdays ["Mo", ..., "So"].
            - datasets (list): ChartJS-style datasets with:
                - label (str): Project and task.
                - data (list): Hours per day.
                - stack (str): Project name.

    Raises:
        400: If start date is invalid.
    """
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


@analysis_bp.route("/export/pdf")
@login_required
def export_pdf():
    """
    Exports time entries to a downloadable PDF.

    Query Parameters:
        start (str, optional): Start date in ISO format (YYYY-MM-DD).
        end (str, optional): End date in ISO format (YYYY-MM-DD).

    Returns:
        Response: PDF file as download.

    Raises:
        400: If date format is invalid.
    """
    start_str = request.args.get("start")
    end_str = request.args.get("end")

    time_entries = load_time_entries()

    # optional time filter
    if start_str and end_str:
        try:
            start = datetime.fromisoformat(start_str)
            end = datetime.fromisoformat(end_str)
            time_entries = filter_time_entries_by_date(time_entries, start, end)
        except ValueError:
            return "Invalid date format (expected YYYY-MM-DD)", 400

    pdf_bytes = export_time_entries_pdf(time_entries)

    return send_file(
        BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name="time_report.pdf",
    )


@analysis_bp.route("/export/csv")
@login_required
def export_csv():
    """
    Exports time entries to a downloadable CSV file.

    Query Parameters:
        start (str, optional): Start date in ISO format (YYYY-MM-DD).
        end (str, optional): End date in ISO format (YYYY-MM-DD).

    Returns:
        Response: CSV file as download.

    Raises:
        400: If date format is invalid.
    """
    entries = load_time_entries()
    # optional time filter
    start_str = request.args.get("start")
    end_str = request.args.get("end")

    if start_str and end_str:
        try:
            start = datetime.fromisoformat(start_str)
            end = datetime.fromisoformat(end_str)
            entries = filter_time_entries_by_date(entries, start, end)
        except ValueError:
            return "Invalid date format. Use YYYY-MM-DD.", 400

    csv_text = export_time_entries_csv(entries)

    response = make_response(csv_text)
    response.headers["Content-Disposition"] = "attachment; filename=time_entries.csv"
    response.headers["Content-Type"] = "text/csv"
    return response


@analysis_bp.route("/overall-progress")
@login_required
def api_overall_progress():
    """
    Get overall progress across all active projects based on completed tasks.

    Returns:
        float: A number between 0 and 1 representing the overall completion ratio.
    """
    tasks = load_tasks()
    from backend.services.analysis_service import overall_progress

    result = overall_progress(tasks)
    return jsonify({"overall_progress": result})


@analysis_bp.route("/check_progress", methods=["POST"])
@login_required
def check_progress():
    """
    Checks the progress of the current user's tasks and detects deviations
    from the expected progress.

    Loads all tasks, optionally calculates the dynamically expected progress
    for the logged-in user, and verifies whether the actual progress is within
    an allowed deviation threshold.

    Returns a JSON response with the status.

    Returns:
        Response: JSON with {"status": "ok"} upon successful check.
    """
    tasks = load_tasks()

    # Dynamische Erwartung berechnen (optional)
    expected = calculate_expected_progress(tasks, current_user.user_id)

    check_progress_deviation(
        tasks, expected_progress=expected, threshold=0.2, user_id=current_user.user_id
    )
    return jsonify({"status": "ok"})
