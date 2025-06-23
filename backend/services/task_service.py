from datetime import timedelta
from flask_login import current_user

from backend.database import db
from backend.models.task import Task, TaskStatus
from backend.models.time_entry import TimeEntry
from backend.models.category import Category
from backend.models.project import Project
from backend.services.project_service import update_total_duration_for_project


def create_task(
    title,
    description=None,
    due_date=None,
    status="todo",
    project_id=None,
    member_id=None,
    category_id=None,
    created_from_tracking=False,
):
    """Create a new task for either a solo project, team project, or as a default task.

    - In solo projects, the task is assigned to the current user (`user_id`).
    - In team projects, only the project admin (creator) may create tasks,
      and they are automatically set as `admin_id`. Optionally, a team member can be assigned (`member_id`).

    Args:
        title (str): The title of the task.
        description (str, optional): A detailed description of the task.
        due_date (datetime, optional): The deadline of the task.
        status (str, optional): Status of the task (default is 'todo').
        project_id (int, optional): ID of the project the task belongs to.
        member_id (int, optional): The ID of the assigned team member (only in team projects).
        category_id (int, optional): ID of the category assigned to the task.
        created_from_tracking (bool, optional): Whether the task was created from time tracking.

    Returns:
        dict: Success message with ID of the created task.
    """

    user_id = None  # Assigned to solo or default tasks
    admin_id = None  # Used only for team projects

    if project_id:
        project = Project.query.get(project_id)
        if not project:
            return {"error": "Project not found."}

        if project.team_id:
            if project.user_id != current_user.user_id:
                return {"error": "Only the project admin can create tasks in this team project."}
            # Teamprojekt
            admin_id = current_user.user_id
        else:
            # Solo-projekt
            user_id = current_user.user_id
    else:
        # Kein Projekt angegeben → Default-Task
        user_id = current_user.user_id

    title = title.strip() if title and title.strip() else "Untitled Task"
    new_task = Task(
        title=title,
        description=description,
        due_date=due_date,
        status=TaskStatus[status],
        project_id=project_id,
        user_id=user_id,
        admin_id=admin_id,
        member_id=member_id,
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


def get_tasks_by_project(project_id):
    """Retrieve all tasks associated with a given project.

    Args:
        project_id (int): The ID of the project.

    Returns:
        list: A list of Task objects.
    """
    return Task.query.filter_by(project_id=project_id).all()


def get_tasks_by_project_for_user(project_id, user_id):
    """
    Returns only the tasks of a project assigned to the given user.
    """
    return Task.query.filter_by(project_id=project_id, member_id=user_id).all()


def update_task(task_id, **kwargs):
    """Update task attributes selectively.

    - Team projects: Only the admin or assigned member can update.
    - Solo/default tasks: Only the owner (user_id) can update.

    Args:
        task_id (int): The ID of the task to update.
        **kwargs: Key-value pairs of fields to update.

    Returns:
        dict: Success or error message with task ID if successful.
    """
    task = Task.query.get(task_id)
    if not task:
        return {"error": "Task not found"}

    if task.project and task.project.team_id:
        if current_user.user_id not in [task.project.user_id, task.member_id]:
            return {"error": "Only the project admin or assigned member can update this task."}
    else:
        if task.user_id != current_user.user_id:
            return {"error": "You are not authorized to update this task."}

    ALLOWED_TASK_FIELDS = [
        "title",
        "description",
        "due_date",
        "status",
        "user_id",
        "member_id",
        "project_id",
        "category_id",
    ]

    old_project_id = task.project_id

    for key, value in kwargs.items():
        if key in ALLOWED_TASK_FIELDS:
            setattr(task, key, value)
    db.session.commit()

    if "project_id" in kwargs:
        if old_project_id and old_project_id != task.project_id:
            update_total_duration_for_project(old_project_id)
        if task.project_id:
            update_total_duration_for_project(task.project_id)

    return {
        "success": True,
        "message": "Task updated successfully",
        "updated_task_id": task_id,
    }


def delete_task(task_id):
    """Delete a task by its ID.

    - Team projects: Only the admin or assigned member can delete.
    - Solo/default tasks: Only the owner (user_id) can delete.

    Args:
        task_id (int): ID of the task to delete.

    Returns:
        dict: Success message or error if not found or not authorized.
    """
    task = Task.query.get(task_id)
    if not task:
        return {"error": "Task not found"}

    if task.project and task.project.team_id:
        if current_user.user_id not in [task.project.user_id, task.member_id]:
            return {"error": "Only the project admin or assigned member can delete this task."}
    else:
        if task.user_id != current_user.user_id:
            return {"error": "You are not authorized to delete this solo task."}

    project_id = task.project_id
    category_id = task.category_id

    db.session.delete(task)
    db.session.commit()

    if project_id:
        update_total_duration_for_project(project_id)

    if category_id:
        task_count = Task.query.filter_by(category_id=category_id).count()
        if task_count == 0:
            Category.query.filter_by(category_id=category_id).delete()
            db.session.commit()

    return {
        "success": True,
        "message": "Task deleted successfully",
        "deleted_task_id": task_id,
    }


def get_tasks_without_time_entries(user_id):
    """Retrieve all tasks that do not have any associated time entries.

    Returns:
        list: A list of Task objects without time entries.
    """
    subquery = db.session.query(TimeEntry.task_id).distinct()

    tasks = (
        Task.query
        .filter(~Task.task_id.in_(subquery))
        .filter(
            (Task.member_id == None) | (Task.member_id == user_id)
        )
        .all()
    )

    return tasks

def get_task_with_time_entries(task_id):
    """Retrieve a task along with all associated time entries.

    Args:
        task_id (int): ID of the task to retrieve.

    Returns:
        dict: Dictionary containing task details and all time entries (if exist),
              or None if the task does not exist.
    """
    task = Task.query.get(task_id)
    if not task:
        return None

    return {
        "task": task.to_dict(),
        "time_entries": (
            [entry.to_dict() for entry in task.time_entries]
            if task.time_entries
            else []
        ),
    }


def get_unassigned_tasks():
    """Retrieve all tasks that are not assigned to any project.

    Returns:
        list: List of Task objects where project_id is None.
    """
    return Task.query.filter(Task.project_id == None).all()


def update_total_duration_for_task(task_id):
    """Recalculate and update the total duration (in seconds) of a task based on all associated time entries.

    Args:
        task_id (int): ID of the task to update.

    Returns:
        dict: Success message with updated duration, or error if task not found.
    """
    task = get_task_by_id(task_id)
    if not task:
        return {"error": "Task not found"}

    total_seconds = sum(
        entry.duration_seconds or 0 for entry in task.time_entries or []
    )
    task.total_duration_seconds = total_seconds
    db.session.commit()

    return {
        "success": True,
        "task_id": task_id,
        "total_duration_seconds": total_seconds,
        "total_duration_formatted": str(timedelta(seconds=total_seconds)),
    }

"""This function also for the new route users/user_id..."""


def get_tasks_assigned_to_user(user_id):
    """Retrieve all tasks assigned to a specific user.

    Args:
        user_id (int): The ID of the user.

    Returns:
        list: A list of Task objects where the user is either owner or assigned member.
    """
    return Task.query.filter(
        (Task.user_id == user_id) | (Task.member_id == user_id)
    ).all()


def unassign_tasks_for_user_in_team(user_id, team_id):
    """
    Unassigns all tasks in the team project that are currently assigned to the specified user.

    Args:
        user_id (int): ID of the user being removed.
        team_id (int): ID of the team whose team project is affected.
    """
    team_project = Project.query.filter_by(team_id=team_id).first()
    if not team_project:
        return

    # Unassign tasks where user is assigned as team member
    tasks_as_member = Task.query.filter_by(
        project_id=team_project.project_id,
        member_id=user_id
    ).all()
    for task in tasks_as_member:
        task.member_id = None

    # Also unassign tasks where user is mistakenly stored as owner (user_id)
    tasks_as_owner = Task.query.filter_by(
        project_id=team_project.project_id,
        user_id=user_id
    ).all()
    for task in tasks_as_owner:
        task.user_id = None

    db.session.commit()


def is_user_authorized_for_task(task, user_id):
    """
    Helper function to check whether the given user is allowed to track time for the task.

    Args:
        task (Task): The task object to check.
        user_id (int): The ID of the current user.

    Returns:
        bool: True if the user is authorized to track this task, False otherwise.
    """
    if not task:
        return False
    if task.member_id:
        return task.member_id == user_id
    return task.user_id == user_id