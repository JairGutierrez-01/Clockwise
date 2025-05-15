from flask_login import login_user as flask_login_user
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
)

from backend.services.token_service import verify_reset_token
from backend.services.user_service import (
    register_user,
    login_user,
    delete_user,
    password_forget,
    edit_user,
    new_password,
)

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """
    Handle user registration.

    Returns:
        str or Response: Redirect to login on success, error message on failure,
        or registration page on GET.
    """
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        password = request.form["password"]
        profile_picture = request.files["profile_picture"]

        result = register_user(
            username, email, first_name, last_name, password, profile_picture
        )

        if "error" in result:
            return result["error"]
        return redirect(url_for("auth.login"))

    return render_template("registerpage.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """
    Handle user login.

    Returns:
        str or Response: Redirect to dashboard on success, error message on failure,
        or login page on GET.
    """
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        result = login_user(username, password)

        if result.get("success"):
            flask_login_user(result["user"])
            return redirect(url_for("dashboard"))
        else:
            return result.get("error", "Login failed.")

    return render_template("loginpage.html")


@auth_bp.route("/user/delete/<int:user_id>", methods=["GET", "POST"])
def user_delete(user_id):
    """
    Handle user deletion.

    Args:
        user_id (int): User id to identify user.
    Returns:
        str or Response: Redirect to dashboard on success, error message on failure,
        or deletion form on GET.
    """
    if request.method == "POST":
        result = delete_user(user_id)

        if result.get("success"):
            return redirect(url_for("dashboard"))
        else:
            return result.get("error", "Delete user failed.")
    return render_template("deleteuser.html", user_id=user_id)


@auth_bp.route("/forgot-password/<token>/<int:user_id>", methods=["GET", "POST"])
def reset_password(token, user_id):
    """
    Handle password reset via token.

    Args:
        token (str): Reset token sent via email.
        user_id (int): User id to indentify user.

    Returns:
        str or Response: Redirect to login on success, error or expired token message,
        or password form on GET.
    """
    email = verify_reset_token(token)
    if not email:
        return "Token is invalid or expired.", 400

    if request.method == "POST":
        password = request.form["password"]
        result = new_password(user_id, password)
        if result.get("success"):
            return redirect(url_for("auth.login"))
        else:
            return "User not found", 404

    return render_template(
        "passwordchange.html", token=token, user_id=user_id, _external=True
    )


@auth_bp.route("/edit/profile/<int:user_id>", methods=["GET", "POST"])
def edit_profile(user_id):
    """
    Handle user profile editing.

    Args:
    user_id(int): User id of the user for identifying.
    Returns:
        str or Response: Redirect to profile page on success, error message on failure,
        or profile editing form on GET.
    """
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        profile_picture = request.files["profile_picture"]
        result = edit_user(
            user_id, username, email, first_name, last_name, password, profile_picture
        )
        if "success" in result:
            return redirect(url_for("auth.profile"))
        else:
            return result.get("error", "Edit profile failed.")
    return render_template("editprofile.html", user_id=user_id)


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    """
    Handle forgot password form.

    Returns:
        str or Response: Confirmation message on success, or form on GET.
    """
    if request.method == "POST":
        email = request.form["email"]
        result = password_forget(email)
        if result.get("success"):
            return "Reset instructions have been sent to your email.."
        else:
            return result.get("error", "Error resetting the password.")

    return render_template("forgotpassword.html")


from flask_login import login_required, current_user
from flask import render_template


@auth_bp.route("/profile")
@login_required
def profile():
    """Render the user profile page.
    This view requires the user to be authenticated.

    Returns:
        Response: A Flask response object that renders the profile page.
    """
    return render_template("profile.html", user=current_user)
