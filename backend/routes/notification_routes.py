from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.database import db
from backend.models.notification import Notification

# Blueprint for notification-related endpoints
notification_bp = Blueprint("notifications", __name__)


@notification_bp.route("/notifications", methods=["GET"])
@jwt_required()
def get_notifications():
    """Returns a list of notifications for the authenticated user."""
    try:
        user_id = get_jwt_identity()

        # Query all notifications for the user, ordered by most recent
        notifications = (
            db.session.query(Notification)
            .filter_by(user_id=user_id)
            .order_by(Notification.created_at.desc())
            .all()
        )

        result = [
            {
                "id": n.id,
                "message": n.message,
                "type": n.type,
                "is_read": n.is_read,
                "created_at": n.created_at.isoformat(),
            }
            for n in notifications
        ]

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
