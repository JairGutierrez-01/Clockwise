from itsdangerous import URLSafeTimedSerializer
from flask import current_app


def generate_reset_token(email):
    """Generate a time-sensitive token for password reset.

    Args:
        email (str): The email address to encode in the token.

    Returns:
        str: A URL-safe, signed token as a string.
    """
    s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    return s.dumps(email, salt="password-reset-salt")


def verify_reset_token(token, expiration=3600):
    """Verify a password reset token and retrieve the associated email.

    Args:
        token (str): The token to be verified.
        expiration (int, optional): Time in seconds before the token expires. Defaults to 3600 (1 hour).

    Returns:
        str or None: The email address if the token is valid; otherwise, None.
    """
    s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    try:
        email = s.loads(token, salt="password-reset-salt", max_age=expiration)
    except Exception:
        return None
    return email
