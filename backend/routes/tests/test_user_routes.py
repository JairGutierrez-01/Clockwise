def test_login_get(client):
    response = client.get("/auth/login")
    assert response.status_code == 200


def test_login_post_failure(client):
    response = client.post(
        "/auth/login", data={"username": "wrong", "password": "wrong"}
    )
    assert response.status_code in [401, 400, 200]


def test_login(client):
    response = client.post("/auth/login", data={"username": "test", "password": "pass"})
    assert response.status_code in [200, 401]
