from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_login import login_required, current_user

from backend.database import db
from backend.models import Notification

# Blueprint for notification-related endpoints
notification_bp = Blueprint("notifications", __name__)


@notification_bp.route("/notifications", methods=["GET"])
@login_required
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


@notification_bp.route("/read/<int:notification_id>", methods=["POST"])
@login_required
def mark_notification_as_read(notification_id):
    """
    Mark a notification as read.

    Only marks if notification belongs to current user and isn't already read.

    Args:
        notification_id (int): ID of the notification to mark as read.

    Returns:
        Response: JSON with success or error message and HTTP status code.
    """
    print(">>> REACHED")
    if not current_user.is_authenticated:
        return jsonify({"error": "Not logged in"}), 403

    notification = Notification.query.get(notification_id)
    if not notification or notification.user_id != current_user.user_id:
        print(">>> Found notification:", notification)
        return jsonify({"error": "No Messags found"}), 404

    if notification.is_read:
        return jsonify({"message": "Already marked as read"}), 200

    notification.is_read = True
    db.session.commit()
    return jsonify({"message": "Message marked as read"}), 200


@notification_bp.route("/delete/<int:notification_id>", methods=["POST"])
@login_required
def delete_notification(notification_id):
    """
    Delete a notification by its ID.

    Only allows deletion if the notification belongs to the current user.

    Args:
        notification_id (int): ID of the notification to delete.

    Returns:
        tuple: Empty response with status code 200 if successful,
               403 if unauthorized,
               404 if notification not found or unauthorized.
    """
    print(">>> REACHED")
    if not current_user.is_authenticated:
        return "", 403

    notification = Notification.query.get(notification_id)
    if notification and notification.user_id == current_user.user_id:  # <- Fix hier
        print(">>> Found notification:", notification)
        db.session.delete(notification)
        db.session.commit()
        return "", 302
    return "", 404
