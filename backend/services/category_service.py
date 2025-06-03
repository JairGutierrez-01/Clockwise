from backend.database import db
from backend.models import Category


def create_category(name):
    """Create a new category.

    Args:
        name (str): The name of the new category.

    Returns:
        dict: Success message and category ID or error if already exists.
    """
    existing = Category.query.filter_by(name=name).first()
    if existing:
        return {"error": "Category already exists."}

    category = Category(name=name)
    db.session.add(category)
    db.session.commit()
    return {"success": True, "category_id": category.category_id}


def get_category(category_id):
    """Retrieve a single category by its ID.

    Args:
        category_id (int): The ID of the category.

    Returns:
        dict: The category object or error if not found.
    """
    category = Category.query.get(category_id)
    if not category:
        return {"error": "Category not found."}
    return {"success": True, "category": category}


def get_all_categories():
    """Retrieve all categories.

    Returns:
        dict: A list of all category objects.
    """
    categories = Category.query.all()
    return {"success": True, "categories": categories}


def update_category(category_id, name):
    """Update the name of a category.

    Args:
        category_id (int): The ID of the category to update.
        name (str): The new name for the category.

    Returns:
        dict: Success message or error if category not found.
    """
    category = Category.query.get(category_id)
    if not category:
        return {"error": "Category not found."}
    category.name = name
    db.session.commit()
    return {"success": True, "message": "Category updated."}


def delete_category(category_id):
    """Delete a category by its ID.

    Args:
        category_id (int): The ID of the category to delete.

    Returns:
        dict: Success message or error if not found.
    """
    category = Category.query.get(category_id)
    if not category:
        return {"error": "Category not found."}
    db.session.delete(category)
    db.session.commit()
    return {"success": True, "message": "Category deleted."}
