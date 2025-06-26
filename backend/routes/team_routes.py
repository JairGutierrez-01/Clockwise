from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required

from backend.database import db
from backend.models import Project, Team, UserTeam, Notification, User
from backend.services.team_service import (
    create_new_team,
    delete_team_and_related,
    check_admin,
    remove_member_from_team,
)
# import the service function with a new name
from backend.services.team_service import get_team_members as get_team_members_service
from backend.services.team_service import get_user_teams as get_user_teams_service

# Create a Flask Blueprint for team-related routes
team_bp = Blueprint("teams", __name__)


@team_bp.route("/", methods=["GET"])
@login_required
def get_user_teams():
    """
    Returns all teams the authenticated user is a member of.

    Returns:
        Response: JSON with teams and current user info or error.
    """
    teams = get_user_teams_service(
        current_user.user_id
    )  # Fetch all teams where current user is member
    return jsonify(
        {
            "current_user": {
                "user_id": current_user.user_id,
                "username": current_user.username,
            },
            "teams": teams,
        }
    )


@team_bp.route("/", methods=["POST"])
@login_required
def create_team():
    """
    Create a new team and assign the current user as admin.

    Returns:
        Response: JSON with new team ID or error message.
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

        # Resolve user_id via username
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

        # Avoid duplicate memberships
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
            return (
                jsonify(
                    {
                        "error": "You do not have permission to remove members from this team"
                    }
                ),
                403,
            )

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
    if not check_admin(current_user.user_id, team_id):
        return jsonify({"error": "Only admins can delete the team"}), 403

    success = delete_team_and_related(team_id)
    if success:
        return jsonify({"success": True}), 200
    return jsonify({"error": "Team not found"}), 404


# unnötig, da anders gelöst?
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


@team_bp.route("/full", methods=["GET"])
@login_required
def get_full_teams():
    """
    Returns full team data for the current user.

    Returns:
        Response: JSON list of teams where the current user is a member.
            Each team includes:
                - Basic info (id, name, description, created_at)
                - List of members with their roles
                - List of projects with status, type, and timing details
    """
    if not current_user.is_authenticated:
        return jsonify({"error": "Not authenticated"}), 401

    user_teams = (
        db.session.query(Team)
        .join(UserTeam)
        .filter(UserTeam.user_id == current_user.user_id)
        .all()
    )

    result = []
    for team in user_teams:
        members = []
        for userteam in team.members:
            members.append(
                {
                    "user_id": userteam.user.user_id,
                    "username": userteam.user.username,
                    "first_name": userteam.user.first_name,
                    "last_name": userteam.user.last_name,
                    "role": userteam.role,
                }
            )

        projects = []
        for project in team.project:
            projects.append(
                {
                    "project_id": project.project_id,
                    "name": project.name,
                    "description": project.description,
                    "type": project.type.name if project.type else None,
                    "status": project.status.name if project.status else None,
                    "time_limit_hours": project.time_limit_hours,
                    "current_hours": project.current_hours or 0,
                    "duration_readable": project.duration_readable,
                    "due_date": (
                        project.due_date.isoformat() if project.due_date else None
                    ),
                }
            )

        result.append(
            {
                "team_id": team.team_id,
                "name": team.name,
                "description": team.description,
                "created_at": team.created_at.isoformat() if team.created_at else None,
                "members": members,
                "projects": projects,
            }
        )

    return jsonify(result)
