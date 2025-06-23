import pytest

from backend.models import Category, User


@pytest.fixture
def setup_category_data(db_session):
    user = User(username="catuser", email="cat@example.com", password_hash="secret")
    db_session.add(user)
    db_session.commit()
    return user


def test_api_get_categories(client, db_session, setup_category_data, login_user):
    user = setup_category_data
    db_session.add(Category(user_id=user.user_id, name="Study"))
    db_session.commit()
    login_user(user)

    res = client.get("/api/categories")
    assert res.status_code == 200
    data = res.get_json()
    assert len(data["categories"]) == 1
    assert data["categories"][0]["name"] == "Study"


def test_api_create_category(client, db_session, setup_category_data, login_user):
    user = setup_category_data
    login_user(user)

    response = client.post("/api/categories", json={"name": "Work"})
    assert response.status_code == 201
    assert Category.query.filter_by(name="Work", user_id=user.user_id).first()


def test_api_create_category_missing_name(client, setup_category_data, login_user):
    user = setup_category_data
    login_user(user)

    response = client.post("/api/categories", json={})
    assert response.status_code == 400
    assert b"Category name is required" in response.data


def test_list_categories(client, db_session, setup_category_data, login_user):
    user = setup_category_data
    login_user(user)
    db_session.add(Category(user_id=user.user_id, name="Uni"))
    db_session.commit()

    response = client.get("/categories")
    assert response.status_code == 200
    assert b"Uni" in response.data


def test_view_category_success(client, db_session, setup_category_data, login_user):
    user = setup_category_data
    login_user(user)
    cat = Category(user_id=user.user_id, name="Books")
    db_session.add(cat)
    db_session.commit()

    response = client.get(f"/category/{cat.category_id}")
    assert response.status_code == 200
    assert b"Books" in response.data


def test_view_category_not_found(client, setup_category_data, login_user):
    login_user(setup_category_data)
    res = client.get("/category/999999")
    assert res.status_code == 404


def test_create_category_route_post(client, setup_category_data, login_user):
    user = setup_category_data
    login_user(user)

    res = client.post(
        "/category/create", data={"name": "Personal"}, follow_redirects=True
    )
    assert res.status_code == 200
    assert Category.query.filter_by(name="Personal", user_id=user.user_id).first()


def test_edit_category_route_post(client, db_session, setup_category_data, login_user):
    user = setup_category_data
    login_user(user)
    category = Category(user_id=user.user_id, name="Old")
    db_session.add(category)
    db_session.commit()

    response = client.post(
        f"/category/edit/{category.category_id}",
        data={"name": "Updated"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert Category.query.get(category.category_id).name == "Updated"


def test_edit_category_route_get(client, db_session, setup_category_data, login_user):
    user = setup_category_data
    login_user(user)
    category = Category(user_id=user.user_id, name="EditMe")
    db_session.add(category)
    db_session.commit()

    res = client.get(f"/category/edit/{category.category_id}")
    assert res.status_code == 200
    assert b"EditMe" in res.data


def test_delete_category_route(client, db_session, setup_category_data, login_user):
    user = setup_category_data
    login_user(user)
    category = Category(user_id=user.user_id, name="DeleteMe")
    db_session.add(category)
    db_session.commit()

    res = client.post(f"/category/delete/{category.category_id}", follow_redirects=True)
    assert res.status_code == 200
    assert not Category.query.get(category.category_id)


def test_delete_category_not_found(client, setup_category_data, login_user):
    login_user(setup_category_data)
    res = client.post("/category/delete/999999")
    assert res.status_code == 404
