import os
import uuid as uuid

from flask import current_app, url_for
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename

from backend.database import db
from backend.models import User
from backend.services.mail_service import send_forgot_password
from backend.services.profile_picture_service import create_profile_picture
from backend.services.token_service import generate_reset_token


def register_user(
    username, email, first_name, last_name, password, profile_picture=None
):
    """Register a new user.

    Args:
        username (str): The desired username.
        email (str): The user's email address.
        first_name (str): The user's first name.
        last_name (str): The user's last name.
        password (str): The user's password.
        profile_picture (FileStorage, optional): An optional profile picture file.

    Returns:
        dict: A success message or an error if the user already exists.
    """
    existing_user = User.query.filter(
        (User.username == username) | (User.email == email)
    ).first()

    if existing_user:
        return {"error": "Username or e-mail already exists."}

    hashed_pw = generate_password_hash(password)
    profile_picture_path = None

    # kürzt filepath -> gibt nur Namen des Bilds weiter
    if profile_picture:
        filename = secure_filename(profile_picture.filename)
        picture_name = f"{uuid.uuid4()}_{filename}"
        relative_path = os.path.join("profile_pictures", picture_name).replace(
            "\\", "/"
        )
        full_path = os.path.join(current_app.static_folder, relative_path)
        profile_picture.save(full_path)
        profile_picture_path = relative_path

    new_user = User(
        username=username,
        email=email,
        password_hash=hashed_pw,
        first_name=first_name,
        last_name=last_name,
        profile_picture=profile_picture_path,  # optional
    )

    db.session.add(new_user)
    db.session.commit()

    return {"success": True, "message": "User registered successfully"}


def login_user(username, password):
    """Authenticate a user by username and password.

    Args:
        username (str): The username of the user.
        password (str): The password to check.

    Returns:
        dict: Success and user object if login is successful, else an error message.
    """
    user = User.query.filter_by(username=username).first()

    if user and check_password_hash(user.password_hash, password):
        return {"success": True, "user": user}
    else:
        return {"success": False, "error": "Invalid username or password."}


def new_password(user_id, password):
    """Set a new password for the user identified by email.

    Args:
        user_id (int): The user identified by email.
        password (str): The new password to set.

    Returns:
        dict: Success if password changed, else an error.
    """
    user = User.query.filter_by(user_id=user_id).first()
    if user:
        user.password_hash = generate_password_hash(password)
        db.session.commit()
        return {"success": True, "user": user}
    else:
        return {"success": False, "error": "Invalid username or password."}


def password_forget(email):
    """Trigger the forgot password process by sending a reset link via email.

    Args:
        email (str): The email address of the user.

    Returns:
        dict: Success if reset email is sent, else an error.
    """
    user = User.query.filter_by(email=email).first()
    if not user:
        return {"error": "E-Mail not found"}
    token = generate_reset_token(user.email)
    reset_url = url_for(
        "auth.reset_password", token=token, user_id=user.user_id, _external=True
    )
    send_forgot_password(email, reset_url)
    return {"success": True, "message": "Password reset instructions sent"}


def delete_user(user_id):
    """Delete a user account by username.

    Args:
        user_id (int): The user id of the account to delete.

    Returns:
        dict: Success message if deleted, else error if user not found.
    """
    user = User.query.filter_by(user_id=user_id).first()
    if not user:
        return {"error": "User not found."}
    db.session.delete(user)
    db.session.commit()
    return {"success": True, "message": "User deleted successfully"}


def edit_user(
    user_id, username, email, first_name, last_name, password, profile_picture=None
):
    """Update a user's account details.

    Args:
        user_id (int): The user_id of the user to identify.
        username (str): The username of the user to update.
        email (str): The new email address (optional).
        first_name (str): The new first name (optional).
        last_name (str): The new last name (optional).
        password (str): The new password (optional).
        profile_picture (FileStorage, optional): A new profile picture file.

    Returns:
        dict: Success message if updated, else error if user not found.
    """
    existing_user = User.query.filter_by(user_id=user_id).first()

    if not existing_user:
        return {"error": "User not found."}
    if username and username != existing_user.username:
        existing_user.username = username

    if email and email != existing_user.email:
        existing_user.email = email

    if first_name and first_name != existing_user.first_name:
        existing_user.first_name = first_name

    if last_name and last_name != existing_user.last_name:
        existing_user.last_name = last_name

    if password:
        existing_user.password_hash = generate_password_hash(password)

    if profile_picture:
        filepath = create_profile_picture(existing_user, profile_picture)
        existing_user.profile_picture = filepath.replace("\\", "/")

    db.session.commit()

    return {"success": True, "message": "User updated successfully"}
