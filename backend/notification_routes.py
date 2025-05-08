from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.database import SessionLocal
from backend.models.notification import Notification

notification_bp = Blueprint('notifications', __name__)

@notification_bp.route('/notifications', methods = ['GET'])
@jwt_required()
def get_notifications():
    session = SessionLocal()
    try:
        user_id = get_jwt_identity()
        notifications = session.query(Notification).filter_by(user_id=user_id).order_by(Notification.created_at.desc()).all()

        result = [
            {
                "id": n.id,
                "message": n.message,
                "type": n.type,
                "is_read": n.is_read,
                "created_at": n.created_at.isoformat()
            } for n in notifications
        ]
        return jsonify(result), 200
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()