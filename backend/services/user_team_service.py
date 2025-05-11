from backend.database import db
from backend.models import User, Team, UserTeam


def add_member(username, teamname, role):
    """
    Add a user as a member to a specific team.

    Args:
        username (str): The username of the user to add.
        teamname (str): The name of the team to which the user will be added.
        role (str): The role to assign to the user in the team.

    Returns:
        dict: A dictionary with success or error message.
    """
    existing_user = User.query.filter(User.username == username).first()
    existing_team = Team.query.filter(Team.name == teamname).first()
    if not existing_user:
        return {"error": "Username doesn't exists."}

    if not existing_team:
        return {"error": "Team doesn't exists."}

    existing_user_team = UserTeam.query.filter_by(
        user_id=existing_user.user_id, team_id=existing_team.team_id
    ).first()
    if existing_user_team:
        return {"error": "User is already a member of this team."}

    user_id = existing_user.user_id
    team_id = existing_team.team_id

    new_user_team = UserTeam(user_id=user_id, team_id=team_id, role=role)
    db.session.add(new_user_team)
    db.session.commit()

    return {"success": True, "message": "Member was added successfully"}
