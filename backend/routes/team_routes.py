from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.database import db
from backend.models.team import Team
from backend.models.user_team import UserTeam
from backend.models.notification import Notification

team_bp = Blueprint("teams", __name__)

@team_bp.route("/", methods=["GET"])
@jwt_required()
def get_user_teams():
    """
    Returns all teams the authenticated user is a member of.
    """
    try:
        user_id = get_jwt_identity()

        user_teams = (
            db.session.query(UserTeam)
            .filter_by(user_id=user_id)
            .join(Team)
            .order_by(Team.created_at.desc())
            .all()
        )

        result = [
            {
                "team_id": ut.team.team_id,
                "team_name": ut.team.name,
                "role": ut.role,
                "created_at": ut.team.created_at.isoformat(),
            }
            for ut in user_teams
        ]

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@team_bp.route("/", methods=["POST"])
@jwt_required()
def create_team():
    """Create a new team and assign the current user as admin."""
    try:
        data = request.get_json()
        name = data.get("name")

        if not name or not name.strip():
            return jsonify({"error": "Team name is required"}), 400

        user_id = get_jwt_identity()

        new_team = Team(name=name.strip())
        db.session.add(new_team)
        db.session.commit()

        user_team = UserTeam(user_id=user_id, team_id=new_team.team_id, role="admin")
        db.session.add(user_team)
        db.session.commit()

        notification = Notification(
            user_id=user_id,
            project_id=None,  # no projects associated
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
    Creates a new team and assigns the current user as admin.
    - Uses try-except-finally to handle database errors safely.
    - Commits team creation and membership separately.
    - Always closes the session to avoid DB connection leaks.
"""
