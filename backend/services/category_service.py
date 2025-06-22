from backend.database import db
from backend.models import Category, Notification


def create_category(name, user_id):
    """Create a new category for a specific user.

    Args:
        name (str): The name of the new category.
        user_id (int): The user ID who owns the category.

    Returns:
        dict: Success message and category ID or error if already exists.
    """
    existing = Category.query.filter_by(name=name, user_id=user_id).first()
    if existing:
        return {"error": "Category already exists."}

    category = Category(name=name, user_id=user_id)
    db.session.add(category)
    db.session.commit()

    notification = Notification(
        user_id=user_id,
        project_id=None,
        message=f"Category created '{category.name}'.",
        type="category",
    )
    db.session.add(notification)
    db.session.commit()
    return {"success": True, "category_id": category.category_id, "name": category.name}


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


def get_all_categories(user_id):
    """Retrieve all categories for a specific user.

    Args:
        user_id (int): The ID of the user.

    Returns:
        dict: A list of category objects.
    """
    categories = Category.query.filter_by(user_id=user_id).all()
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
