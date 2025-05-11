from werkzeug.security import generate_password_hash

from flask import current_app, url_for
from backend.database import db
from backend.models import User
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
import uuid as uuid
import os

from backend.services.mail_service import send_forgot_password

# from backend.services.mail_service import send_forgot_password
from backend.services.profile_picture_service import create_profile_picture
from backend.services.token_service import generate_reset_token


# from backend.services.token_service import generate_reset_token


def register_user(
    username, email, first_name, last_name, password, profile_picture=None
):
    existing_user = User.query.filter(
        (User.username == username) | (User.email == email)
    ).first()

    if existing_user:
        return {"error": "Username or e-mail already exists."}

    hashed_pw = generate_password_hash(password)
    profile_picture_path = None

    if profile_picture:
        profile_picture_filename = secure_filename(profile_picture.filename)
        picture_name = str(uuid.uuid1()) + "_" + profile_picture_filename
        filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], picture_name)
        profile_picture.save(filepath)
        profile_picture_path = filepath

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
    user = User.query.filter_by(username=username).first()

    if user and check_password_hash(user.password_hash, password):
        return {"success": True, "user": user}
    else:
        return {"success": False, "error": "Invalid username or password."}


def new_password(email, password):
    user = User.query.filter_by(email.email).first()
    if user:
        user.password_hash = generate_password_hash(password)
        db.session.commit()
        return {"success": True, "user": user}
    else:
        return {"success": False, "error": "Invalid username or password."}


""""""


# TODO: forgot password
def password_forget(email):
    user = User.query.filter_by(email=email).first()
    if not user:
        return {"error": "E-Mail not found"}

    token = generate_reset_token(user.email)
    reset_url = url_for("auth.reset_password", token=token, _external=True)
    send_forgot_password(email, reset_url)
    return {"success": True, "message": "Password reset instructions sent"}


# TODO: delete user
def delete_user(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        return {"error": "User not found."}
    db.session.delete(user)
    db.session.commit()
    return {"success": True, "message": "User deleted successfully"}


# TODO: edit user
def edit_user(username, email, first_name, last_name, password, profile_picture=None):
    existing_user = User.query.filter((User.username == username)).first()

    if not existing_user:
        return {"error": "User not found."}

    if email and email != existing_user.email:
        existing_user.email = email

    if first_name and first_name != existing_user.first_name:
        existing_user.first_name = first_name

    if last_name and last_name != existing_user.last_name:
        existing_user.last_name = last_name

    if password:
        existing_user.password_hash = generate_password_hash(password)

    if existing_user.profile_picture and os.path.exists(existing_user.profile_picture):
        filepath = create_profile_picture(existing_user, profile_picture)

        existing_user.profile_picture = filepath

    db.session.commit()

    return {"success": True, "message": "User updated successfully"}
