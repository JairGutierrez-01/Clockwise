from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
)

from backend.services.user_team_service import add_member

team_bp = Blueprint("team", __name__)


@team_bp.route("/team/members", methods=["GET", "POST"])
def members():
    """
    Handle adding members to a team.

    Methods:
        GET: Render the team member management page.
        POST: Add a member to a team using form data.

    Form Data:
        username (str): The username of the member to add.
        teamname (str): The name of the team.
        role (str): The role assigned to the member.

    Returns:
        Response: Redirects to the same page on success, or displays an error on failure.
    """
    if request.method == "POST":
        username = request.form["username"]
        teamname = request.form["teamname"]
        role = request.form["role"]

        result = add_member(username, teamname, role)

        if result.get("success"):
            session["user_id"] = result["user"].user_id
            return redirect(url_for("team.members"))
        else:
            return result.get("error", "Adding of member failed.")

    return render_template("team.html")
