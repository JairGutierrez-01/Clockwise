from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.database import db
from backend.models.notification import Notification

# Blueprint for notification-related endpoints
notification_bp = Blueprint("notifications", __name__)


# For CHANTAL:
# Endpoint: GET /notifications
# Returns all notifications for the current user
# Optional frontend usage:
#    - To get all notifications:
#         GET /notifications
#    - To get only unread notifications:
#         GET /notifications?unread=true
@notification_bp.route("/notifications", methods=["GET"])
@jwt_required()
def get_notifications():
    """Returns a list of notifications for the authenticated user."""
    try:
        user_id = get_jwt_identity()

        # Optional: only get unread notifications
        only_unread = request.args.get("unread") == "true"

        query = db.session.query(Notification).filter_by(user_id=user_id)
        if only_unread:
            query = query.filter_by(is_read=False)

        notifications = query.order_by(Notification.created_at.desc()).all()

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


# For CHANTAL:
# Endpoint: PATCH /notifications/<notification_id>
# Marks a single notification as "read"
# Frontend usage:
#    - After user clicks a notification:
#         PATCH /notifications/5
#    - Requires JWT token in Authorization header
@notification_bp.route("/notifications/<int:notification_id>", methods=["PATCH"])
@jwt_required()
def mark_notification_as_read(notification_id):
    """Mark a specific notification as read."""
    user_id = get_jwt_identity()

    notification = Notification.query.filter_by(
        id=notification_id, user_id=user_id
    ).first()

    if not notification:
        return jsonify({"error": "Notification not found"}), 404

    if notification.is_read:
        return jsonify({"message": "Notification already marked as read"}), 200

    notification.is_read = True
    db.session.commit()

    return jsonify({"message": "Notification marked as read"}), 200
