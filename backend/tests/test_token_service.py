import time

import pytest
from flask import Flask

from backend.services.token_service import generate_reset_token, verify_reset_token


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "test-secret-key"
    with app.app_context():
        yield app


def test_generate_and_verify_token(app):
    email = "test@example.com"

    token = generate_reset_token(email)
    assert isinstance(token, str)

    result = verify_reset_token(token)
    assert result == email

    from itsdangerous import URLSafeTimedSerializer

    s = URLSafeTimedSerializer("wrong-secret")
    wrong_token = s.dumps(email, salt="password-reset-salt")
    assert verify_reset_token(wrong_token) is None

    short_expiration = 1
    time.sleep(2)

    expired_result = verify_reset_token(token, expiration=short_expiration)
    assert expired_result is None

    assert verify_reset_token("randominvalidtoken") is None
