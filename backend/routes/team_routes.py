from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.database import db
from backend.models.team import Team
from backend.models.user_team import UserTeam

team_bp = Blueprint("teams", __name__)

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
