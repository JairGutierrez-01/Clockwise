from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.database import SessionLocal
from backend.models.team import Team
from backend.models.user_team import UserTeam

team_bp = Blueprint('teams', __name__)

@team_bp.route('/teams', methods=['POST'])
@jwt_required()
def create_team():
    session = SessionLocal()
    try: #create a new sesion for the Database
        data = request.get_json()
        name = data.get('name')

        if not name or not name.strip():
            return jsonify({'Error': 'Team name is required'}), 400

        user_id = get_jwt_identity()

# - Create team
        new_team = Team(name=name.strip())
        session.add(new_team)
        session.commit()

# - User as admin
        user_team = UserTeam(user_id=user_id, team_id=new_team.id, role='admin')
        session.add(user_team)
        session.commit()

        return jsonify({'message': 'Team created', 'team_id': new_team.id}), 201

    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

"""
    Creates a new team and assigns the current user as admin.
    - Uses try-except-finally to handle database errors safely.
    - Commits team creation and membership separately.
    - Always closes the session to avoid DB connection leaks.
"""