from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from backend.services.category_service import (
    create_category,
    get_all_categories,
)

category_bp = Blueprint("category", __name__)


@category_bp.route("/api/categories", methods=["GET"])
@login_required
def api_get_categories():
    """
    Retrieves all categories for the currently authenticated user.

    Returns:
        Response: A JSON response with a list of categories, each including:
            - category_id (int): The ID of the category.
            - name (str): The name of the category.
    """
    result = get_all_categories(current_user.user_id)
    categories = result.get("categories", [])
    return jsonify(
        {
            "categories": [
                {"category_id": cat.category_id, "name": cat.name} for cat in categories
            ]
        }
    )


@category_bp.route("/api/categories", methods=["POST"])
@login_required
def api_create_category():
    """
    Creates a new category for the authenticated user.

    Request JSON Body:
        name (str): The name of the new category.

    Returns:
        Response:
            - 400: If the category name is missing.
            - 200: If an error occurs during creation.
            - 201: On successful creation.
    """
    data = request.get_json()
    name = data.get("name", "").strip()

    if not name:
        return jsonify({"error": "Category name is required"}), 400

    result = create_category(name, current_user.user_id)
    if "error" in result:
        return jsonify(result), 200

    return jsonify(result), 201
