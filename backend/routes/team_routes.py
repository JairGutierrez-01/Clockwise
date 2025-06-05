from flask import Blueprint, request, jsonify
from flask_login import current_user
from backend.database import db
from backend.models.team import Team
from backend.models.user_team import UserTeam
from backend.models.notification import Notification
from backend.models.user import User # Ensure User model is imported
from backend.services.team_service import (
    check_admin, is_team_member,
    create_team_project, create_task_for_team_project
)
# Create a Flask Blueprint for team-related routes
team_bp = Blueprint("teams", __name__)


@team_bp.route("/", methods=["GET"])
def get_user_teams():
    """Returns all teams the authenticated user is a member of."""
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

        result_teams = [  # Renamed variable
            {
                "team_id": ut.team.team_id,
                "team_name": ut.team.name,
                "role": ut.role,
                "created_at": ut.team.created_at.isoformat(),
            }
            for ut in user_teams
        ]

        # Include current user's info in the response
        current_user_info = None
        if current_user.is_authenticated:
            current_user_info = {
                "user_id": current_user.user_id,
                "username": current_user.username,
            }

        # Return a dictionary containing both teams and current_user info
        return jsonify({"teams": result_teams, "current_user": current_user_info}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@team_bp.route("/", methods=["POST"])
def create_team():
    """Create a new team and assign the current user as admin."""
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


@team_bp.route("/users/<int:user_id>", methods=["GET"])
def get_user_details(user_id):
    """Returns details for a specific user by ID."""
    print(f"DEBUG: get_user_details called for user_id: {user_id}")
    if not current_user.is_authenticated:
        print("DEBUG: User not authenticated in get_user_details.")
        return jsonify({"error": "Not authenticated"}), 401

    try:
        # CHANGED THIS LINE: Use filter_by instead of get()
        user = User.query.filter_by(user_id=user_id).first()
        print(f"DEBUG: User query result for {user_id}: {user}") # This will show if user is found

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
def add_team_member(team_id):
    if not current_user.is_authenticated:
        return jsonify({"error": "Not authenticated"}), 401

    try:
        user_id = current_user.user_id
        data = request.get_json()

        raw_user_input = data.get("user_id")
        if not raw_user_input:
            return jsonify({"error": "No user_id or username provided"}), 400

        # If it's a number, use it directly
        if str(raw_user_input).isdigit():
            new_member_id = int(raw_user_input)
        else:
            # Otherwise, treat it as a username and resolve to user_id
            user = User.query.filter_by(username=raw_user_input.strip()).first()
            if not user:
                return jsonify({"error": f"User '{raw_user_input}' not found"}), 404
            new_member_id = user.user_id

        role = data.get("role", "member").strip().lower()

        # Check admin rights
        admin_relation = UserTeam.query.filter_by(
            user_id=user_id, team_id=team_id, role="admin"
        ).first()
        if not admin_relation:
            return jsonify({"error": "You do not have permission to add members to this team"}), 403

        # Check if user already a member
        existing = UserTeam.query.filter_by(user_id=new_member_id, team_id=team_id).first()
        if existing:
            return jsonify({"error": "User is already a member"}), 400

        # Add new member
        new_member = UserTeam(user_id=new_member_id, team_id=team_id, role=role)
        db.session.add(new_member)
        db.session.commit()

        return jsonify({"message": "Member added successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@team_bp.route("/<int:team_id>/remove-member", methods=["PATCH"])
def remove_team_member(team_id):
    if not current_user.is_authenticated:
        return jsonify({"error": "Not authenticated"}), 401

    try:
        user_id = current_user.user_id
        data = request.get_json()

        raw_user_input = data.get("user_id")
        if not raw_user_input:
            return jsonify({"error": "No user_id or username provided"}), 400

        if str(raw_user_input).isdigit():
            member_id = int(raw_user_input)
        else:
            user = User.query.filter_by(username=raw_user_input.strip()).first()
            if not user:
                return jsonify({"error": f"User '{raw_user_input}' not found"}), 404
            member_id = user.user_id

        # Check admin rights
        admin_relation = UserTeam.query.filter_by(
            user_id=user_id, team_id=team_id, role="admin"
        ).first()
        if not admin_relation:
            return jsonify({"error": "You do not have permission to remove members from this team"}), 403

        # Check if target user is actually in the team
        relation = UserTeam.query.filter_by(user_id=member_id, team_id=team_id).first()
        if not relation:
            return jsonify({"error": "User is not a member of this team"}), 404

        # Remove the member
        db.session.delete(relation)
        db.session.commit()

        return jsonify({"message": "Member removed successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@team_bp.route("/<int:team_id>/members", methods=["GET"]) # Corrected route path
def get_team_members(team_id):
    if not current_user.is_authenticated:
        return jsonify({"error": "Not authenticated"}), 401

    relation = UserTeam.query.filter_by(user_id=current_user.user_id, team_id=team_id).first()
    if not relation:
        return jsonify({"error": "You are not a member of this team"}), 403

    members = UserTeam.query.filter_by(team_id=team_id).all()
    result = [
        {"user_id": m.user_id, "role": m.role}
        for m in members
    ]
    return jsonify(result), 200


@team_bp.route("/<int:team_id>", methods=["DELETE"])
def delete_team(team_id):
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


@team_bp.route("/teams/<int:team_id>/projects", methods=["POST"])
def api_create_team_project(team_id):
    if not current_user.is_authenticated:
        return jsonify({"error": "Not authenticated"}), 401

    if not check_admin(current_user.user_id, team_id):
        return jsonify({"error": "Only admins can create team projects"}), 403

    data = request.get_json()
    name = data.get("name")
    description = data.get("description", "")

    if not name:
        return jsonify({"error": "Project name is required"}), 400

    result = create_team_project(name, description, team_id)
    return jsonify(result), 201


@team_bp.route("/projects/<int:project_id>/tasks", methods=["POST"])
def api_create_team_task(project_id):
    if not current_user.is_authenticated:
        return jsonify({"error": "Not authenticated"}), 401

    data = request.get_json()
    name = data.get("name")
    category_id = data.get("category_id")
    assigned_user_id = data.get("assigned_user_id")

    if not name or not category_id:
        return jsonify({"error": "Name and category_id are required"}), 400

    result = create_task_for_team_project(name, category_id, project_id, assigned_user_id)
    return jsonify(result), 201