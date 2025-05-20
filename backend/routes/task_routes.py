from flask import Blueprint, render_template, request, redirect, url_for
from backend.services.task_service import (
    create_task,
    get_task_by_id,
    get_task_by_project,
    get_default_tasks,
    update_task,
    delete_task,
)

task_bp = Blueprint("tasks", __name__)


@task_bp.route("/tasks")
def task_list():
    """Display a list of tasks.

    If a project ID is provided via query parameters, only tasks belonging to that
    project are shown. Otherwise, default tasks (without a project) are listed.

    Returns:
        Response: Rendered HTML page with a list of tasks.
    """
    project_id_str = request.args.get("project_id")
    if project_id_str:
        project_id = int(project_id_str)
        tasks = get_task_by_project(project_id)
    else:
        tasks = get_default_tasks()
    return render_template("task_list.html", tasks=tasks)


@task_bp.route("/tasks/create", methods=["GET", "POST"])
def task_create():
    """Handle the creation of a new task.

    GET: Render the task creation form.
    POST: Create the task and redirect to task list.

    Returns:
        Response: Form page on GET, redirect to task list on POST.
    """
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        if not title:
            title = "Untitled task"

        description = request.form.get("description")
        due_date = request.form.get("due_date")
        status = request.form.get("status", "todo")
        project_id = request.form.get("project_id")
        user_id = request.form.get("user_id")

        create_task(
            title=title,
            description=description,
            due_date=due_date,
            status=status,
            project_id=project_id,
            user_id=user_id,
        )
        return redirect(url_for("tasks.task_list"))

    return render_template("task_form.html")


@task_bp.route("/tasks/edit/<int:task_id>", methods=["GET", "POST"])
def task_edit(task_id):
    """Edit an existing task.

    Args:
        task_id (int): ID of the task to edit.

    Returns:
        Response: Render edit form on GET, perform update on POST.
    """
    task = get_task_by_id(task_id)
    if not task:
        return "Task not found", 404

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        if not title:
            title = "Untitled task"

        update_task(
            task_id,
            title=title,
            description=request.form.get("description"),
            due_date=request.form.get("due_date"),
            status=request.form.get("status", "todo"),
            project_id=request.form.get("project_id"),
            user_id=request.form.get("user_id"),
        )
        return redirect(url_for("tasks.task_list"))

    return render_template("task_form.html")


@task_bp.route("/tasks/delete/<int:task_id>", methods=["POST"])
def task_delete(task_id):
    """Delete a task.

    Args:
        task_id (int): ID of the task to delete.

    Returns:
        Response: Redirects to the task list after deletion.
    """
    delete_task(task_id)
    return redirect(url_for("tasks.task_list"))
