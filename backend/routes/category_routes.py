from flask import Blueprint, request, redirect, url_for, render_template, jsonify
from flask_login import login_required, current_user

from backend.services.category_service import (
    create_category,
    get_category,
    get_all_categories,
    update_category,
    delete_category,
)

category_bp = Blueprint("category", __name__)


@category_bp.route("/api/categories", methods=["GET"])
@login_required
def api_get_categories():
    result = get_all_categories(current_user.id)
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
    data = request.get_json()
    name = data.get("name", "").strip()

    if not name:
        return jsonify({"error": "Category name is required"}), 400

    result = create_category(name, current_user.id)
    if "error" in result:
        return jsonify(result), 200

    return jsonify(result), 201


@category_bp.route("/categories", methods=["GET"])
@login_required
def list_categories():
    """Display all available categories.

    Returns:
        Response: Renders a template with all categories.
    """
    result = get_all_categories(current_user.id)
    return render_template("category_list.html", categories=result["categories"])


@category_bp.route("/category/<int:category_id>", methods=["GET"])
@login_required
def view_category(category_id):
    """Display a single category.

    Args:
        category_id (int): ID of the category.

    Returns:
        Response: Renders a template with category details or error.
    """
    result = get_category(category_id)
    if "success" in result:
        return render_template("category_detail.html", category=result["category"])
    return result["error"], 404


@category_bp.route("/category/create", methods=["GET", "POST"])
@login_required
def create_category_route():
    """Treat creation of a new category.

    Returns:
        Response: Redirect on success or show form.
    """
    if request.method == "POST":
        name = request.form["name"]
        result = create_category(name, current_user.id)
        if "success" in result:
            return redirect(url_for("category.list_categories"))
        return result["error"]
    return render_template("category_create.html")


@category_bp.route("/category/edit/<int:category_id>", methods=["GET", "POST"])
@login_required
def edit_category_route(category_id):
    """Edit an existing category.

    Args:
        category_id (int): ID of the category to edit.

    Returns:
        Response: Form or redirect after successful update.
    """
    if request.method == "POST":
        name = request.form["name"]
        result = update_category(category_id, name)
        if "success" in result:
            return redirect(url_for("category.list_categories"))
        return result["error"]

    result = get_category(category_id)
    if "success" in result:
        return render_template("category_edit.html", category=result["category"])
    return result["error"], 404


@category_bp.route("/category/delete/<int:category_id>", methods=["POST"])
@login_required
def delete_category_route(category_id):
    """Delete a category.

    Args:
        category_id (int): ID of the category to delete.

    Returns:
        Response: Redirect or error.
    """
    result = delete_category(category_id)
    if "success" in result:
        return redirect(url_for("category.list_categories"))
    return result["error"], 404
