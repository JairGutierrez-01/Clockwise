from unittest.mock import patch

import pytest

from backend.models import Category, User


@pytest.fixture
def setup_category_data(db_session):
    """
    Creates and commits a test user for category-related API tests.

    Args:
        db_session (Session): SQLAlchemy database session fixture.

    Returns:
        User: The created user instance persisted in the test database.
    """
    user = User(
        user_id=999,
        username="Joe",
        email="joe@example.com",
        password_hash="secret",
        first_name="Joe",
        last_name="Doe",
    )
    db_session.add(user)
    db_session.commit()
    return user


def test_api_get_categories(client, db_session, setup_category_data):
    """
    Test retrieving categories for the logged-in user via GET /api/categories.

    Adds a category to the database and checks if it is returned by the API.

    Args:
        client (FlaskClient): The Flask test client.
        db_session (Session): SQLAlchemy database session.
        setup_category_data (User): Fixture that provides a test user.

    Asserts:
        - Response status code is 200 (OK).
        - Response JSON contains the added category with the correct name.
    """
    user = setup_category_data
    db_session.add(Category(user_id=user.user_id, name="Study"))
    db_session.commit()

    with patch("flask_login.utils._get_user") as mock_user:
        mock_user.return_value = user
        res = client.get("/api/categories")
        assert res.status_code == 200
        data = res.get_json()
        assert len(data["categories"]) == 1
        assert data["categories"][0]["name"] == "Study"


def test_api_create_category(client, db_session, setup_category_data):
    """
    Test creating a new category via POST /api/categories for the logged-in user.

    Sends a valid category name and verifies the category is stored.

    Args:
        client (FlaskClient): The Flask test client.
        db_session (Session): SQLAlchemy database session.
        setup_category_data (User): Fixture that provides a test user.

    Asserts:
        - Response status code is 201 (Created).
        - The category is persisted in the database for the user.
    """
    user = setup_category_data
    with patch("flask_login.utils._get_user") as mock_user:
        mock_user.return_value = user
        response = client.post("/api/categories", json={"name": "Work"})
        assert response.status_code == 201
        assert Category.query.filter_by(name="Work", user_id=user.user_id).first()


def test_api_create_category_missing_name(client, setup_category_data):
    """
    Test API returns error 400 when trying to create a category without a name.

    Sends a POST request with missing 'name' field in JSON payload.

    Args:
        client (FlaskClient): The Flask test client.
        setup_category_data (User): Fixture that provides a test user.

    Asserts:
        - Response status code is 400 (Bad Request).
        - Response contains an error message about missing category name.
    """
    user = setup_category_data

    response = client.post("/api/categories", json={})
    assert response.status_code == 400
    assert b"Category name is required" in response.data
