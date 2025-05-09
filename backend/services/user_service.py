from werkzeug.security import generate_password_hash
from backend.database import db
from backend.models import User
from werkzeug.security import check_password_hash


def register_user(username, email, first_name, last_name, password):
    existing_user = User.query.filter(
        (User.username == username) | (User.email == email)
    ).first()

    if existing_user:
        return {"error": "Username or e-mail already exists."}

    hashed_pw = generate_password_hash(password)

    new_user = User(
        username=username,
        email=email,
        password_hash=hashed_pw,
        first_name=first_name,
        last_name=last_name,
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


# TODO: forgot password
# TODO: send e-mail
# TODO: delete user
