import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database import Base
from datetime import datetime

from backend.models.task import Task, TaskStatus


@pytest.fixture(scope="function")
def db_session():
    """Creates a fresh in-memory DB session for each test."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_create_task(db_session):
    """Test creating and retrieving a Task."""
    task = Task(
        title="Sample Task",
        description="This is a test task",
        due_date=datetime(2025, 6, 20),
        status=TaskStatus.todo,
        created_from_tracking=False,
        total_duration_seconds=120,
    )

    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    fetched = db_session.query(Task).filter_by(title="Sample Task").first()
    assert fetched is not None
    assert fetched.task_id is not None
    assert fetched.title == "Sample Task"
    assert fetched.status == TaskStatus.todo
    assert fetched.created_from_tracking is False
    assert fetched.total_duration_seconds == 120


def test_task_repr(db_session):
    """Test __repr__ output of a Task."""
    task = Task(title="Repr Task")
    db_session.add(task)
    db_session.commit()
    result = repr(task)
    assert "<Task(" in result
    assert "Repr Task" in result


def test_task_total_duration_property():
    """Test the formatted total_duration string."""
    task = Task(total_duration_seconds=3661)  # 1 hour, 1 minute, 1 second
    assert task.total_duration == "1:01:01"


def test_task_to_dict(db_session):
    """Test conversion of a Task to dict format."""
    due = datetime(2025, 6, 20)
    task = Task(
        title="Dict Task",
        description="desc",
        due_date=due,
        status=TaskStatus.in_progress,
        created_from_tracking=True,
        total_duration_seconds=90,
    )
    db_session.add(task)
    db_session.commit()
    task_dict = task.to_dict()

    assert task_dict["title"] == "Dict Task"
    assert task_dict["description"] == "desc"
    assert task_dict["due_date"] == due.strftime("%Y-%m-%d")
    assert task_dict["status"] == "in_progress"
    assert task_dict["created_from_tracking"] is True
    assert task_dict["total_duration_seconds"] == 90
    assert "total_duration" in task_dict
