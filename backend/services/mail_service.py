from flask_mail import Mail, Message

mail = Mail()


def send_forgot_password(email, reset_url):
    """Send a password reset email to the user.

    Args:
        email (str): The recipient's email address.
        reset_url (str): The URL the user can click to reset their password.

    Returns:
        None
    """
    message = Message(
        subject="Reset Your Password",
        recipients=[email],
        sender=("Clockwise", "sep.clockwise@gmail.com"),
    )
    message.html = f"""<p>Hello,</p>
<p>you have submitted a request to reset your password.</p>
<p><a href="{reset_url}">Click here to reset your password</a></p>
<p>If you were not, you can ignore this message.</p>
<p>Best regards,<br>your Clockwise team</p>
"""
    mail.send(message)
