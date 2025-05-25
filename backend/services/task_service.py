from backend.database import db
from backend.models.task import Task, TaskStatus
from backend.models.time_entry import TimeEntry


def create_task(
    title,
    description=None,
    due_date=None,
    status="todo",
    project_id=None,
    user_id=None,
    category_id=None,
    created_from_tracking=False,
):
    """Create a new task with optional project, user, and category assignment.

    Args:
        title (str): The title of the task.
        description (str, optional): A detailed description of the task.
        due_date (datetime, optional): The deadline of the task.
        status (str, optional): Status of the task (default is 'todo').
        project_id (int, optional): ID of the project the task belongs to.
        user_id (int, optional): ID of the user assigned to the task.
        category_id (int, optional): ID of the category assigned to the task.
        created_from_tracking (bool, optional): Whether the task was created from time tracking.

    Returns:
        dict: Success message with ID of the created task.
    """
    new_task = Task(
        title=title or "Untitled Task",
        description=description,
        due_date=due_date,
        status=TaskStatus[status],
        project_id=project_id,
        user_id=user_id,
        category_id=category_id,
        created_from_tracking=created_from_tracking,
    )
    db.session.add(new_task)
    db.session.commit()
    return {
        "success": True,
        "message": "Task created successfully",
        "task_id": new_task.task_id,
    }


def get_task_by_id(task_id):
    """Retrieve a task by its ID.

    Args:
        task_id (int): ID of the task to retrieve.

    Returns:
        Task: The task object, or None if not found.
    """
    return Task.query.get(task_id)


def get_task_by_project(project_id):
    """Retrieve all tasks associated with a given project.

    Args:
        project_id (int): The ID of the project.

    Returns:
        list: A list of Task objects.
    """
    return Task.query.filter_by(project_id=project_id).all()


def get_default_tasks():
    """Retrieve all default tasks (not assigned to any project).

    Returns:
        list: A list of Task objects without project assignments.
    """
    return Task.query.filter_by(project_id=None).all()


def update_task(task_id, **kwargs):
    """Update task attributes selectively.

    Args:
        task_id (int): The ID of the task to update.
        **kwargs: Key-value pairs of fields to update.

    Returns:
        dict: Success or error message with task ID if successful.
    """
    task = Task.query.get(task_id)
    if not task:
        return {"error": "Task not found"}

    ALLOWED_TASK_FIELDS = [
        "title",
        "description",
        "due_date",
        "status",
        "user_id",
        "project_id",
        "category_id",
    ]

    for key, value in kwargs.items():
        if key in ALLOWED_TASK_FIELDS:
            setattr(task, key, value)
    db.session.commit()
    return {
        "success": True,
        "message": "Task updated successfully",
        "updated_task_id": task_id,
    }


def delete_task(task_id):
    """Delete a task by its ID.

    Args:
        task_id (int): ID of the task to delete.

    Returns:
        dict: Success message or error if not found.
    """
    task = Task.query.get(task_id)
    if not task:
        return {"error": "Task not found"}
    db.session.delete(task)
    db.session.commit()
    return {
        "success": True,
        "message": "Task deleted successfully",
        "deleted_task_id": task_id,
    }


def get_tasks_without_time_entries():
    """Retrieve all tasks that do not have any associated time entries.

    This is useful for displaying tasks that are available for new time tracking.

    Returns:
        list: A list of Task objects without any time entries.
    """
    return (
        Task.query.outerjoin(Task.time_entries).filter(Task.time_entries == None).all()
    )


def get_task_with_time_entry(task_id):
    """Retrieve a task along with its associated time entry.

    Args:
        task_id (int): ID of the task to retrieve.

    Returns:
        dict: Dictionary containing task details and its time entry (if exists),
              or None if the task does not exist.
    """
    task = Task.query.get(task_id)
    if not task:
        return None

    return {
        "task": task.to_dict(),
        "time_entry": task.time_entries.to_dict() if task.time_entries else None,
    }
