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
    forgot_password,
    edit_user,
    new_password,
)

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
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
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        result = login_user(username, password)

        if result.get("success"):
            session["user_id"] = result["user"].user_id
            return redirect(url_for("dashboard"))
        else:
            return result.get("error", "Login failed.")

    return render_template("loginpage.html")


@auth_bp.route("/user/delete", methods=["GET", "POST"])
def user_delete():
    if request.method == "POST":
        username = request.form["username"]
        result = delete_user(username)

        if result.get("success"):
            return redirect(url_for("dashboard"))
        else:
            return result.get("error", "Delete user failed.")
    return render_template("deleteuser.html")


@auth_bp.route("/entertoken/<token>", methods=["GET", "POST"])
def reset_password(token):
    email = verify_reset_token(token)
    if not email:
        return "Token is invalid or expired.", 400

    if request.method == "POST":
        password = request.form["password"]
        result = new_password(email, password)
        if result.get("success"):
            return redirect(url_for("auth.login"))
        else:
            return "User not found", 404

    return render_template("forgotpassword.html")


@auth_bp.route("/edit/profile", methods=["GET", "POST"])
def edit_profile():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        profile_picture = request.files["profile_picture"]
        result = edit_user(
            username, email, first_name, last_name, password, profile_picture
        )
        if "success" in result:
            return redirect(url_for("profile"))
        else:
            return result.get("error", "Edit profile failed.")
    return render_template("editprofile.html")
