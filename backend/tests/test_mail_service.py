from unittest.mock import patch

import pytest
from flask import Flask

from backend.services.mail_service import send_forgot_password


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["MAIL_SERVER"] = "localhost"
    app.config["MAIL_PORT"] = 25
    app.config["MAIL_DEFAULT_SENDER"] = "sep.clockwise@gmail.com"
    with app.app_context():
        yield app


def test_send_forgot_password(app):
    with patch("backend.services.mail_service.mail.send") as mock_send:
        email = "test@example.com"
        reset_url = "http://example.com/reset?token=abc123"

        send_forgot_password(email, reset_url)

        mock_send.assert_called_once()
        sent_message = mock_send.call_args[0][0]
        assert email in sent_message.recipients
        assert reset_url in sent_message.html
        assert sent_message.subject == "Reset Your Password"
        sender = sent_message.sender
        if isinstance(sender, tuple):
            sender_name = sender[0]
        else:
            sender_name = sender.split(" <")[0]
        assert sender_name == "Clockwise"
