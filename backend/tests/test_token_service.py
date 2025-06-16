import time

import pytest
from flask import Flask

from backend.services.token_service import generate_reset_token, verify_reset_token


@pytest.fixture
def app():
    """Creates and configures a Flask test application.

    Yields:
        Flask: A Flask application instance with test configuration.
    """
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "test-secret-key"
    with app.app_context():
        yield app


def test_generate_and_verify_token(app):
    """Test generating and verifying a reset token.

    This test covers:
    - Generating a token from an email.
    - Verifying the token returns the original email.
    - Verifying with a wrong secret returns None.
    - Verifying an expired token returns None.
    - Verifying a completely invalid token returns None.

    Args:
        app (Flask): The Flask test app fixture with a secret key.
    """
    email = "test@example.com"

    # Generate token
    token = generate_reset_token(email)
    assert isinstance(token, str)

    # Verify valid token
    result = verify_reset_token(token)
    assert result == email

    # Verify with incorrect secret
    from itsdangerous import URLSafeTimedSerializer

    s = URLSafeTimedSerializer("wrong-secret")
    wrong_token = s.dumps(email, salt="password-reset-salt")
    assert verify_reset_token(wrong_token) is None

    # Verify expired token
    short_expiration = 1  # second
    time.sleep(2)  # wait for token to expire
    expired_result = verify_reset_token(token, expiration=short_expiration)
    assert expired_result is None

    # Verify completely invalid token
    assert verify_reset_token("randominvalidtoken") is None
