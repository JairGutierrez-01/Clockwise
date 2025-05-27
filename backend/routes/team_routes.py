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

@team_bp.route("/<int:team_id>/add-member", methods=["PATCH"])
@jwt_required()
def add_team_member(team_id):
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        new_member_id = data.get("user_id")
        role = data.get("role", "member")

        admin_relation = UserTeam.query.filter_by(user_id=user_id, team_id=team_id, role="admin").first()
        if not admin_relation:
            return jsonify({"error": "You do not have permission to add members to this team"}), 403

        # verifies if is already a member
        existing = UserTeam.query.filter_by(user_id=new_member_id, team_id=team_id).first()
        if existing:
            return jsonify({"error": "User is already a member"}), 400

        new_member = UserTeam(user_id=new_member_id, team_id=team_id, role=role)
        db.session.add(new_member)
        db.session.commit()

        return jsonify({"message": "Member added successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@team_bp.route("/<int:team_id>/remove-member", methods=["PATCH"])
@jwt_required()
def remove_team_member(team_id):
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        member_id = data.get("user_id")

        admin_relation = UserTeam.query.filter_by(user_id=user_id, team_id=team_id, role="admin").first()
        if not admin_relation:
            return jsonify({"error": "You do not have permission to remove members from this team"}), 403

        relation = UserTeam.query.filter_by(user_id=member_id, team_id=team_id).first()
        if not relation:
            return jsonify({"error": "User is not a member of this team"}), 404

        db.session.delete(relation)
        db.session.commit()

        return jsonify({"message": "Member removed successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# this part can be optional but could be good to have it
@team_bp.route("/<int:team_id>/members", methods=["GET"])
@jwt_required()
def get_team_members(team_id):
    try:
        user_id = get_jwt_identity()

        # verifies if user is part of the team
        relation = UserTeam.query.filter_by(user_id=user_id, team_id=team_id).first()
        if not relation:
            return jsonify({"error": "You are not a member of this team"}), 403

        members = UserTeam.query.filter_by(team_id=team_id).all()
        result = [
            {
                "user_id": member.user_id,
                "role": member.role
            }
            for member in members
        ]

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
