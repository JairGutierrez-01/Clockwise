import csv
import numbers
from collections import defaultdict
from datetime import datetime, timedelta

import pytest

from backend.services.analysis_service import (
    export_time_entries_pdf,
    export_time_entries_csv,
    filter_time_entries_by_date,
    aggregate_weekly_time,
    calendar_events,
    progress_per_project,
    actual_target_comparison,
    tasks_in_month,
    aggregate_time_by_day_project_task,
)


@pytest.fixture
def sample_time_entries():
    now = datetime.now()
    return [
        {
            "start": now - timedelta(days=1, hours=3),
            "end": now - timedelta(days=1, hours=2),
            "task": "Test Task 1",
            "project": "Test Project A",
        },
        {
            "start": now - timedelta(hours=1, minutes=30),
            "end": now - timedelta(hours=1),
            "task": "Another Task 2 with a very long name that will be truncated",
            "project": None,
        },
    ]


@pytest.fixture
def sample_tasks():
    return [
        {
            "project": "Test Project A",
            "status": "done",
            "title": "Task 1",
            "due_date": None,
        },
        {
            "project": "Test Project A",
            "status": "open",
            "title": "Task 2",
            "due_date": None,
        },
        {"project": None, "status": "done", "title": "Task 3", "due_date": None},
    ]


@pytest.fixture
def sample_target():
    return {"Test Project A": 10.0, "Other Project": 5.0}


def test_export_time_entries_pdf_returns_bytes(sample_time_entries):
    pdf_data = export_time_entries_pdf(sample_time_entries)
    assert isinstance(pdf_data, bytes)
    assert len(pdf_data) > 100


def test_export_time_entries_csv_contains_header_and_rows(sample_time_entries):
    csv_text = export_time_entries_csv(sample_time_entries)
    lines = csv_text.strip().splitlines()
    assert lines[0] == "Start,End,Task,Project"
    assert len(lines) == len(sample_time_entries) + 1
    reader = csv.DictReader(lines)
    rows = list(reader)
    assert rows[0]["Task"] == "Test Task 1"
    assert rows[1]["Project"] == ""


def test_filter_time_entries_by_date(sample_time_entries):
    start_date = datetime.now() - timedelta(days=2)
    end_date = datetime.now()
    filtered = filter_time_entries_by_date(sample_time_entries, start_date, end_date)
    assert len(filtered) == len(sample_time_entries)
    filtered_empty = filter_time_entries_by_date(
        sample_time_entries,
        datetime.now() + timedelta(days=1),
        datetime.now() + timedelta(days=2),
    )
    assert filtered_empty == []


def test_aggregate_weekly_time(sample_time_entries):
    week_start = datetime.now() - timedelta(days=datetime.now().weekday())
    result = aggregate_weekly_time(sample_time_entries, week_start)
    assert isinstance(result, defaultdict)
    for project, hours_list in result.items():
        assert len(hours_list) == 7
        import numbers

        assert all(isinstance(h, numbers.Real) for h in hours_list)


def test_calendar_events(sample_time_entries):
    events = calendar_events(sample_time_entries)
    assert isinstance(events, list)
    assert "title" in events[0]
    assert "start" in events[0]
    assert "end" in events[0]


def test_progress_per_project(sample_tasks):
    progress = progress_per_project(sample_tasks)
    assert isinstance(progress, dict)
    assert "Test Project A" in progress
    assert 0 <= progress["Test Project A"] <= 1


def test_actual_target_comparison(sample_time_entries, sample_target):
    comparison = actual_target_comparison(sample_time_entries, sample_target)
    assert isinstance(comparison, dict)
    for proj, vals in comparison.items():
        assert "actual" in vals
        assert "target" in vals
        assert isinstance(vals["actual"], (int, float))
        assert isinstance(vals["target"], (int, float))


def test_tasks_in_month(sample_tasks):
    now = datetime.now()
    sample_tasks[0]["start_date"] = now
    filtered = tasks_in_month(sample_tasks, now.year, now.month)
    assert sample_tasks[0] in filtered
    filtered_empty = tasks_in_month(sample_tasks, 2000, 1)
    assert filtered_empty == []


def test_aggregate_time_by_day_project_task(sample_time_entries):
    week_start = datetime.now() - timedelta(days=datetime.now().weekday())
    agg = aggregate_time_by_day_project_task(sample_time_entries, week_start)
    assert isinstance(agg, defaultdict)
    for (project, task), hours_list in agg.items():
        assert isinstance(project, str)
        assert isinstance(task, str)
        assert len(hours_list) == 7
        assert all(isinstance(h, numbers.Real) for h in hours_list)
