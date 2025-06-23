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
    user = User(username="catuser", email="cat@test.com", password_hash="123")
    db_session.add(user)
    db_session.commit()
    return user


def test_create_category_success(db_session, setup_user):
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
    user = setup_user
    create_category("Uni", user.user_id)

    result = create_category("Uni", user.user_id)
    assert "error" in result
    assert result["error"] == "Category already exists."


def test_create_category_invalid_name(db_session, setup_user):
    user = setup_user

    result = create_category("!!!", user.user_id)
    assert "error" in result
    assert result["error"] == "Category name is invalid or empty."


def test_get_category_success(db_session, setup_user):
    user = setup_user
    cat = Category(name="Lernen", user_id=user.user_id)
    db_session.add(cat)
    db_session.commit()

    result = get_category(cat.category_id)
    assert result["success"] is True
    assert result["category"].name == "Lernen"


def test_get_category_not_found():
    result = get_category(999999)
    assert "error" in result
    assert result["error"] == "Category not found."


def test_get_all_categories(db_session, setup_user):
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
    user = setup_user
    cat = Category(name="OldName", user_id=user.user_id)
    db_session.add(cat)
    db_session.commit()

    result = update_category(cat.category_id, "NewName")
    assert result["success"]
    assert Category.query.get(cat.category_id).name == "NewName"


def test_update_category_not_found():
    result = update_category(99999, "Nothing")
    assert result["error"] == "Category not found."


def test_delete_category_success(db_session, setup_user):
    user = setup_user
    cat = Category(name="ToDelete", user_id=user.user_id)
    db_session.add(cat)
    db_session.commit()

    result = delete_category(cat.category_id)
    assert result["success"]
    assert Category.query.get(cat.category_id) is None


def test_delete_category_not_found():
    result = delete_category(404)
    assert result["error"] == "Category not found."
