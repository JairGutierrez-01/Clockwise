import pytest

from backend.models import Category, User
from backend.services.category_service import (
    create_category,
    get_category,
    get_all_categories,
    update_category,
    delete_category,
)


@pytest.fixture
def setup_user(db_session):
    """Create and return a sample user for testing.

    Args:
        db_session (Session): Database session fixture.

    Returns:
        User: A new user instance added to the database.
    """
    user = User(
        username="catuser",
        email="cat@test.com",
        password_hash="123",
        first_name="Test",
        last_name="User",
    )
    db_session.add(user)
    db_session.commit()
    return user


def test_create_category_success(db_session, setup_user):
    """Test successful creation of a new category.

    Args:
        db_session (Session): Database session fixture.
        setup_user (User): User fixture for associating the category.

    Asserts:
        The result indicates success.
        The created category exists in the database with expected name.
    """
    user = setup_user
    result = create_category("Persönliche Projekte", user.user_id)

    assert result["success"] is True
    assert "category_id" in result
    category = Category.query.get(result["category_id"])
    assert (
        category.name == "Persoenliche Projekte"
        or category.name == "Persönliche Projekte"
    )


def test_create_category_already_exists(db_session, setup_user):
    """Test error when creating a category with a name that already exists.

    Args:
        db_session (Session): Database session fixture.
        setup_user (User): User fixture.

    Asserts:
        The result contains an error with appropriate message.
    """
    user = setup_user
    create_category("Uni", user.user_id)

    result = create_category("Uni", user.user_id)
    assert "error" in result
    assert result["error"] == "Category already exists."


def test_create_category_invalid_name(db_session, setup_user):
    """Test error when creating a category with an invalid name.

    Args:
        db_session (Session): Database session fixture.
        setup_user (User): User fixture.

    Asserts:
        The result contains an error indicating invalid or empty name.
    """
    user = setup_user

    result = create_category("!!!", user.user_id)
    assert "error" in result
    assert result["error"] == "Category name is invalid or empty."


def test_get_category_success(db_session, setup_user):
    """Test successful retrieval of a category by ID.

    Args:
        db_session (Session): Database session fixture.
        setup_user (User): User fixture.

    Asserts:
        The result indicates success.
        The returned category has the expected name.
    """
    user = setup_user
    cat = Category(name="Lernen", user_id=user.user_id)
    db_session.add(cat)
    db_session.commit()

    result = get_category(cat.category_id)
    assert result["success"] is True
    assert result["category"].name == "Lernen"


def test_get_category_not_found(db_session):
    """
    Test that retrieving a category by a non-existing ID returns an error.

    Args:
        db_session: The database session fixture to manage transactions.

    Asserts:
        The result contains an error indicating that the category was not found.
    """
    with db_session.begin():  # opens a transaction and thus an active session
        result = get_category(999999)  # function call with active session
    assert "error" in result


def test_get_all_categories(db_session, setup_user):
    """Test retrieval of all categories for a given user.

    Args:
        db_session (Session): Database session fixture.
        setup_user (User): User fixture.

    Asserts:
        The result indicates success.
        The returned list contains all categories for the user.
    """
    user = setup_user
    db_session.add_all(
        [
            Category(name="X", user_id=user.user_id),
            Category(name="Y", user_id=user.user_id),
        ]
    )
    db_session.commit()

    result = get_all_categories(user.user_id)
    assert result["success"]
    assert len(result["categories"]) == 2


def test_update_category_success(db_session, setup_user):
    """Test successful update of an existing category's name.

    Args:
        db_session (Session): Database session fixture.
        setup_user (User): User fixture.

    Asserts:
        The result indicates success.
        The category's name is updated in the database.
    """
    user = setup_user
    cat = Category(name="OldName", user_id=user.user_id)
    db_session.add(cat)
    db_session.commit()

    result = update_category(cat.category_id, "NewName")
    assert result["success"]
    assert Category.query.get(cat.category_id).name == "NewName"


def test_update_category_not_found(db_session):
    """Test error when updating a non-existing category.

    Asserts:
        The result contains an error indicating category not found.
    """
    with db_session.begin():  # opens a transaction and thus an active session
        result = update_category(99999, "Nothing")  # function call with active session
    assert result["error"] == "Category not found."


def test_delete_category_success(db_session, setup_user):
    """Test successful deletion of a category.

    Args:
        db_session (Session): Database session fixture.
        setup_user (User): User fixture.

    Asserts:
        The result indicates success.
        The category no longer exists in the database.
    """
    user = setup_user
    cat = Category(name="ToDelete", user_id=user.user_id)
    db_session.add(cat)
    db_session.commit()

    result = delete_category(cat.category_id)
    assert result["success"]
    assert Category.query.get(cat.category_id) is None


def test_delete_category_not_found(db_session):
    """Test error when deleting a non-existing category.

    Asserts:
        The result contains an error indicating category not found.
    """
    result = delete_category(404)
    assert result["error"] == "Category not found."
