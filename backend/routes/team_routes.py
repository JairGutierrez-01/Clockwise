from flask import Blueprint, request, jsonify, url_for
from flask_login import current_user, login_required

from backend.database import db
from backend.models import Project, Team, UserTeam, Task, Notification, User
from backend.services.team_service import (
    create_new_team,
    delete_team_and_related,
    is_team_member,
    check_admin,
    remove_member_from_team,
)

from backend.services.team_service import get_team_members as get_team_members_service
from backend.services.team_service import get_user_teams as get_user_teams_service

# Create a Flask Blueprint for team-related routes
team_bp = Blueprint("teams", __name__)


@team_bp.route("/", methods=["GET"])
@login_required
def get_user_teams():
    """
    Returns all teams the authenticated user is a member of.

    Args:
        None

    Returns:
        Response: JSON with teams and current user info or error.
    """
    """
    if not current_user.is_authenticated:
        return jsonify({"error": "Not authenticated"}), 401

    try:
        user_id = current_user.user_id

        user_teams = (
            db.session.query(UserTeam)
            .filter_by(user_id=user_id)
            .join(Team)
            .order_by(Team.created_at.desc())
            .all()
        )

        result_teams = [
            {
                "team_id": ut.team.team_id,
                "team_name": ut.team.name,
                "role": ut.role,
                "created_at": ut.team.created_at.isoformat(),
            }
            for ut in user_teams
        ]

        current_user_info = None
        if current_user.is_authenticated:
            current_user_info = {
                "user_id": current_user.user_id,
                "username": current_user.username,
            }

        return jsonify({"teams": result_teams, "current_user": current_user_info}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    """
    teams = get_user_teams_service(current_user.user_id)
    return jsonify({"current_user": {
        "user_id": current_user.user_id,
        "username": current_user.username
    }, "teams": teams})


@team_bp.route("/", methods=["POST"])
@login_required
def create_team():
    """
    Create a new team and assign the current user as admin.

    Args:
        None

    Returns:
        Response: JSON with new team ID or error message.
    """
    """
    if not current_user.is_authenticated:
        return jsonify({"error": "Not authenticated"}), 401

    try:
        data = request.get_json()
        name = data.get("name")

        if not name or not name.strip():
            return jsonify({"error": "Team name is required"}), 400

        user_id = current_user.user_id

        new_team = Team(name=name.strip())
        db.session.add(new_team)
        db.session.commit()

        user_team = UserTeam(user_id=user_id, team_id=new_team.team_id, role="admin")
        db.session.add(user_team)
        db.session.commit()

        notification = Notification(
            user_id=user_id,
            project_id=None,
            message=f"Team created '{new_team.name}'.",
            type="team",
        )
        db.session.add(notification)
        db.session.commit()

        return jsonify({"message": "Team created", "team_id": new_team.team_id}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

"""
    data = request.get_json()
    name = data.get("name")
    if not name:
        return jsonify({"error": "Missing team name"}), 400

    result = create_new_team(name, current_user.user_id)
    return jsonify(result), 201



@team_bp.route("/users/<int:user_id>", methods=["GET"])
@login_required
def get_user_details(user_id):
    """
    Get details of a specific user.

    Args:
        user_id (int): The ID of the user to retrieve.

    Returns:
        Response: JSON with user information or error message.
    """
    print(f"DEBUG: get_user_details called for user_id: {user_id}")
    if not current_user.is_authenticated:
        print("DEBUG: User not authenticated in get_user_details.")
        return jsonify({"error": "Not authenticated"}), 401

    try:
        # CHANGED THIS LINE: Use filter_by instead of get()
        user = User.query.filter_by(user_id=user_id).first()
        print(f"DEBUG: User query result for {user_id}: {user}")

        if not user:
            print(f"DEBUG: User not found in DB for user_id: {user_id}")
            return jsonify({"error": "User not found"}), 404

        print(f"DEBUG: Found user: {user.username} (ID: {user.user_id})")
        return (
            jsonify(
                {
                    "user_id": user.user_id,
                    "username": user.username,
                }
            ),
            200,
        )

    except Exception as e:
        print(f"DEBUG: Exception in get_user_details: {e}")
        return jsonify({"error": str(e)}), 500
    """
    user = get_user_by_id(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"username": user.username})
    """



@team_bp.route("/<int:team_id>/add-member", methods=["PATCH"])
@login_required
def add_team_member(team_id):
    """
    Add a new user to the specified team.

    Args:
        team_id (int): ID of the target team.

    Returns:
        Response: JSON message on success or error.
    """
    if not current_user.is_authenticated:
        return jsonify({"error": "Not authenticated"}), 401

    try:
        user_id = current_user.user_id
        data = request.get_json()

        raw_user_input = data.get("user_id")
        if not raw_user_input:
            return jsonify({"error": "No user_id or username provided"}), 400

        if str(raw_user_input).isdigit():
            new_member_id = int(raw_user_input)
        else:
            user = User.query.filter_by(username=raw_user_input.strip()).first()
            if not user:
                return jsonify({"error": f"User '{raw_user_input}' not found"}), 404
            new_member_id = user.user_id

        role = data.get("role", "member").strip().lower()

        admin_relation = UserTeam.query.filter_by(
            user_id=user_id, team_id=team_id, role="admin"
        ).first()
        if not admin_relation:
            return (
                jsonify(
                    {"error": "You do not have permission to add members to this team"}
                ),
                403,
            )

        existing = UserTeam.query.filter_by(
            user_id=new_member_id, team_id=team_id
        ).first()
        if existing:
            return jsonify({"error": "User is already a member"}), 400

        new_member = UserTeam(user_id=new_member_id, team_id=team_id, role=role)
        db.session.add(new_member)
        db.session.commit()

        team_name = Team.query.filter_by(team_id=team_id).first().name
        notification = Notification(
            user_id=new_member_id,
            project_id=None,
            message=f"You were added to the team '{team_name}'",
            type="team",
        )
        print(f"Creating notification for user {new_member_id}")
        db.session.add(notification)
        db.session.commit()

        return jsonify({"message": "Member added successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@team_bp.route("/<int:team_id>/remove-member", methods=["PATCH"])
@login_required
def remove_team_member(team_id):
    """
    Remove a user from the specified team.
    Also unassigns the user from any tasks in the team's project.

    Args:
        team_id (int): ID of the team.

    Returns:
        Response: JSON success message or error.
    """
    if not current_user.is_authenticated:
        return jsonify({"error": "Not authenticated"}), 401

    try:
        data = request.get_json()
        raw_user_input = data.get("user_id")

        if not raw_user_input:
            return jsonify({"error": "No user_id or username provided"}), 400

        # Get target user ID (from username or ID)
        if str(raw_user_input).isdigit():
            member_id = int(raw_user_input)
        else:
            user = User.query.filter_by(username=raw_user_input.strip()).first()
            if not user:
                return jsonify({"error": f"User '{raw_user_input}' not found"}), 404
            member_id = user.user_id

        # Admin check
        admin_relation = UserTeam.query.filter_by(
            user_id=current_user.user_id, team_id=team_id, role="admin"
        ).first()
        if not admin_relation:
            return jsonify({"error": "You do not have permission to remove members from this team"}), 403

        # Call service
        success = remove_member_from_team(member_id, team_id)
        if not success:
            return jsonify({"error": "User is not a member of this team"}), 404

        return jsonify({"message": "Member removed successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500



@team_bp.route("/<int:team_id>/members", methods=["GET"])  # Corrected route path
@login_required
def get_team_members(team_id):
    """
    Get all members of a team.

    Args:
        team_id (int): ID of the team.

    Returns:
        Response: JSON list of team members or error.
    """
    """
    if not current_user.is_authenticated:
        return jsonify({"error": "Not authenticated"}), 401

    relation = UserTeam.query.filter_by(
        user_id=current_user.user_id, team_id=team_id
    ).first()
    if not relation:
        return jsonify({"error": "You are not a member of this team"}), 403

    members = UserTeam.query.filter_by(team_id=team_id).all()
    result = [{"user_id": m.user_id, "role": m.role} for m in members]
    return jsonify(result), 200
    """
    members = get_team_members_service(team_id)
    return jsonify(members)

@team_bp.route("/<int:team_id>", methods=["DELETE"])
@login_required
def delete_team(team_id):
    """
    Delete a team if the user is an admin.

    Args:
        team_id (int): ID of the team to delete.

    Returns:
        Response: JSON message on success or failure.
    """
    """
    if not current_user.is_authenticated:
        return jsonify({"error": "Not authenticated"}), 401

    try:
        user_id = current_user.user_id

        relation = UserTeam.query.filter_by(
            user_id=user_id, team_id=team_id, role="admin"
        ).first()
        if not relation:
            return (
                jsonify({"error": "You do not have permission to delete this team"}),
                403,
            )

        UserTeam.query.filter_by(team_id=team_id).delete()

        team = Team.query.get(team_id)
        if team:
            db.session.delete(team)
            db.session.commit()
            return jsonify({"message": "Team deleted successfully"}), 200
        else:
            return jsonify({"error": "Team not found"}), 404

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    """
    if not check_admin(current_user.user_id, team_id):
        return jsonify({"error": "Only admins can delete the team"}), 403

    success = delete_team_and_related(team_id)
    if success:
        return jsonify({"success": True}), 200
    return jsonify({"error": "Team not found"}), 404



@team_bp.route("/<int:team_id>/assign_project", methods=["POST"])
@login_required
def api_assign_project_to_team(team_id):
    """
    Assign an existing project to a team.

    Args:
        team_id (int): ID of the team.

    Returns:
        Response: JSON with assignment result or error.
    """
    """
    if not current_user.is_authenticated:
        return jsonify({"error": "Not authenticated"}), 401

    is_admin = UserTeam.query.filter_by(
        user_id=current_user.user_id, team_id=team_id, role="admin"
    ).first()
    if not is_admin:
        return jsonify({"error": "Only admins can assign projects to teams"}), 403

    data = request.get_json()
    if not data or "project_id" not in data:
        return jsonify({"error": "Missing project_id"}), 400

    try:
        project_id = int(data["project_id"])
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid project_id"}), 400

    project = Project.query.filter_by(project_id=project_id, team_id=None).first()
    if not project:
        return jsonify({"error": "Project not found or already assigned"}), 404

    project.team_id = team_id
    db.session.commit()

    return (
        jsonify(
            {
                "success": True,
                "message": "Project assigned to team",
                "project_id": project_id,
                "team_id": team_id,
            }
        ),
        200,
    )
    """
    if not check_admin(current_user.user_id, team_id):
        return jsonify({"error": "Only admins can assign projects to teams"}), 403

    data = request.get_json()
    project_id = data.get("project_id")
    if not project_id:
        return jsonify({"error": "Missing project_id"}), 400

    project = Project.query.filter_by(project_id=project_id, team_id=None).first()
    if not project:
        return jsonify({"error": "Project not found or already assigned"}), 404

    project.team_id = team_id
    db.session.commit()

    return jsonify({"success": True, "message": "Project assigned to team"}), 200



# noch zu implementieren!!
@team_bp.route("/<int:team_id>/tasks", methods=["GET"])
@login_required
def get_tasks_for_team(team_id):
    """
    Get all tasks for the specified team.

    Args:
        team_id (int): ID of the team.

    Returns:
        Response: JSON list of tasks or error.
    """
    if not current_user.is_authenticated:
        return jsonify({"error": "Not authenticated"}), 401

    relation = UserTeam.query.filter_by(
        user_id=current_user.user_id, team_id=team_id
    ).first()
    if not relation:
        return jsonify({"error": "You are not a member of this team"}), 403

    tasks = (
        db.session.query(Task)
        .join(Project, Task.project_id == Project.project_id)
        .filter(Project.team_id == team_id)
        .all()
    )

    return (
        jsonify(
            [
                {
                    "task_id": t.task_id,
                    "title": t.title,
                    "project_id": t.project_id,
                    "assigned_user_id": t.assigned_user_id,
                    "category_id": t.category_id,
                    "status": t.status,
                }
                for t in tasks
            ]
        ),
        200,
    )

# unnötig
@team_bp.route("/<int:team_id>/assign_tasks_to_members", methods=["POST"])
@login_required
def api_assign_tasks_to_members(team_id):
    """
    Admins assign the tasks of project to specific team members.

    Args:
        team_id (int): ID of the team.

    Returns:
        JSON: Success or Error
    """
    if not current_user.is_authenticated:
        return jsonify({"error": "Not authenticated"}), 401

    is_admin = UserTeam.query.filter_by(
        user_id=current_user.user_id, team_id=team_id, role="admin"
    ).first()
    if not is_admin:
        return jsonify({"error": "Only admins can assign tasks"}), 403

    data = request.get_json()
    print("POST /api_assign_tasks_to_members -> data:", data)
    if not data or "project_id" not in data or "assignments" not in data:
        return jsonify({"error": "Missing project_id or assignments"}), 400

    try:
        project_id = int(data["project_id"])
        assignments = data["assignments"]
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid data format"}), 400

    project = Project.query.filter_by(project_id=project_id, team_id=team_id).first()
    if not project:
        return jsonify({"error": "Project not found or does not belong to team"}), 404

    # user_ids = {u.user_id for u in UserTeam.query.filter_by(team_id=team_id).all()}

    updated_tasks = []
    for entry in assignments:
        task_id = entry.get("task_id")
        user_id = entry.get("user_id")

        if not isinstance(task_id, int) or not isinstance(user_id, int):
            continue

        if not is_team_member(user_id, team_id):
            continue

        task = Task.query.filter_by(task_id=task_id, project_id=project_id).first()
        if not task:
            continue

        task.assigned_user_id = user_id
        updated_tasks.append(task_id)

    db.session.commit()

    return jsonify({
        "success": True,
        "updated_tasks": updated_tasks,
        "team_id": team_id,
        "project_id": project_id
    }), 200


# brauch nicht
@team_bp.route("/full", methods=["GET"])
@login_required
def api_get_user_teams_with_members_and_projects():
    """
    Get user teams including members and their projects.

    Args:
        None

    Returns:
        Response: JSON list of teams with members and projects.
    """
    if not current_user.is_authenticated:
        return jsonify({"error": "Not authenticated"}), 401

    user_id = current_user.user_id
    user_teams = db.session.query(UserTeam).filter_by(user_id=user_id).join(Team).all()

    result = []
    for ut in user_teams:
        team = ut.team
        members = (
            db.session.query(UserTeam).filter_by(team_id=team.team_id).join(User).all()
        )
        member_data = [
            {"user_id": m.user.user_id, "username": m.user.username, "role": m.role}
            for m in members
            if m.user
        ]

        projects = Project.query.filter_by(team_id=team.team_id).all()
        project_data = [
            {
                "project_id": p.project_id,
                "name": p.name,
                "description": p.description,
                "time_limit_hours": p.time_limit_hours,
                "current_hours": p.current_hours or 0,
                "duration_readable": p.duration_readable,
                "due_date": p.due_date.isoformat() if p.due_date else None,
                "title": p.name,
                "date": p.due_date.strftime("%Y-%m-%d") if p.due_date else None,
                "color": "#f44336",
            }
            for p in projects
        ]

        result.append(
            {
                "team_id": team.team_id,
                "team_name": team.name,
                "role": ut.role,
                "created_at": team.created_at.isoformat(),
                "members": member_data,
                "projects": project_data,
            }
        )

    return jsonify(result), 200
