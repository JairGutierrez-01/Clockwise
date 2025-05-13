from flask import (
    Blueprint, 
    request, 
    redirect, 
    url_for, 
    render_template
)
from backend.services.category_service import (
    create_category,
    get_category,
    get_all_categories,
    update_category,
    delete_category,
)

category_bp = Blueprint("category", __name__)

@category_bp.route("/categories", methods=["GET"])
def list_categories():
    """Display all available categories.

    Returns:
        Response: Renders a template with all categories.
    """
    result = get_all_categories()
    return render_template("category_list.html", categories=result["categories"])

@category_bp.route("/category/<int:category_id>", methods=["GET"])
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
def create_category_route():
    """Treat creation of a new category.

    Returns:
        Response: Redirect on success or show form.
    """
    if request.method == "POST":
        name = request.form["name"]
        result = create_category(name)
        if "success" in result:
            return redirect(url_for("category.list_categories"))
        return result["error"]
    return render_template("category_create.html")

@category_bp.route("/category/edit/<int:category_id>", methods=["GET", "POST"])
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
