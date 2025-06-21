from backend.database import db
from backend.models.team import Team
from backend.models.user_team import UserTeam
from backend.models.notification import Notification
from backend.models.user import User
from backend.models.project import Project
from backend.models.task import Task
from backend.services.notifications import notify_user_added_to_team
from backend.services.task_service import unassign_tasks_for_user_in_team


def get_user_teams(user_id):
    """Fetches all teams a user belongs to.

    Args:
        user_id (int): ID of the user.

    Returns:
        list: List of team dictionaries with ID, name, role, and creation date.
    """
    user_teams = (
        db.session.query(UserTeam)
        .filter_by(user_id=user_id)
        .join(Team)
        .order_by(Team.created_at.desc())
        .all()
    )

    return [
        {
            "team_id": ut.team.team_id,
            "team_name": ut.team.name,
            "role": ut.role,
            "created_at": ut.team.created_at.isoformat(),
        }
        for ut in user_teams
    ]


def create_new_team(name, user_id):
    """Creates a new team and assigns the user as admin.

    Args:
        name (str): Name of the team.
        user_id (int): ID of the user creating the team.

    Returns:
        dict: Contains message and new team ID.
    """
    new_team = Team(name=name.strip())
    db.session.add(new_team)
    db.session.commit()

    user_team = UserTeam(user_id=user_id, team_id=new_team.team_id, role="admin")
    db.session.add(user_team)
    db.session.commit()

    notification = Notification(
        user_id=user_id,
        project_id=None,
        message=f"Team created '{new_team.name}'.",
        type="team",
    )
    db.session.add(notification)
    db.session.commit()

    return {"team_id": new_team.team_id, "message": "Team created"}

# unnötig?
def get_user_by_id(user_id):
    """Fetch a user by ID.

    Args:
        user_id (int): ID of the user.

    Returns:
        User: User object or None.
    """
    return User.query.filter_by(user_id=user_id).first()

# unnötig?
def resolve_user_id(raw_user_input):
    """Resolves user ID from user ID or username.

    Args:
        raw_user_input (str|int): User ID or username.

    Returns:
        int|None: User ID if found, else None.
    """
    if str(raw_user_input).isdigit():
        return int(raw_user_input)
    user = User.query.filter_by(username=raw_user_input.strip()).first()
    if user:
        return user.user_id
    return None


def check_admin(user_id, team_id):
    """Checks if the user is an admin of the team.

    Args:
        user_id (int): ID of the user.
        team_id (int): ID of the team.

    Returns:
        UserTeam|None: Admin relation or None.
    """
    return UserTeam.query.filter_by(
        user_id=user_id, team_id=team_id, role="admin"
    ).first()


def is_team_member(user_id, team_id):
    """Checks if the user is a member of the team.

    Args:
        user_id (int): ID of the user.
        team_id (int): ID of the team.

    Returns:
        UserTeam|None: Membership relation or None.
    """
    return UserTeam.query.filter_by(user_id=user_id, team_id=team_id).first()

# brauch ich nicht?
def add_member_to_team(user_id, team_id, role):
    """Adds a user to the team with a role.

    Args:
        user_id (int): ID of the user to add.
        team_id (int): ID of the team.
        role (str): Role of the user.

    Returns:
        bool: True if successful.
    """
    new_member = UserTeam(user_id=user_id, team_id=team_id, role=role)
    team = Team.query.filter_by(team_id=team_id).first()
    db.session.add(new_member)
    db.session.commit()

    team_name = Team.query.filter_by(team_id=team_id).first().name
    notification = Notification(
        user_id=user_id,
        project_id=None,
        message=f"You were added to the team '{team_name}'",
        type="team",
    )
    print(f"Creating notification for user {user_id}")
    db.session.add(notification)
    db.session.commit()

    notify_user_added_to_team(user_id, team_name)
    return True

# nötig!
def remove_member_from_team(user_id, team_id):
    """Removes a user from a team and unassigns their tasks.

    Args:
        user_id (int): ID of the user to remove.
        team_id (int): ID of the team.

    Returns:
        bool: True if removed, False otherwise.
    """
    relation = UserTeam.query.filter_by(user_id=user_id, team_id=team_id).first()
    if not relation:
        return False  # User is not a member

    # Unassign all tasks assigned to this user in the team's project
    unassign_tasks_for_user_in_team(user_id, team_id)

    # Remove membership from the UserTeam table
    db.session.delete(relation)
    db.session.commit()
    return True

def get_team_members(team_id):
    """Retrieves all members of a team.

    Args:
        team_id (int): ID of the team.

    Returns:
        list: List of members with user ID and role.
    """
    members = UserTeam.query.filter_by(team_id=team_id).all()
    return [{"user_id": m.user_id, "role": m.role} for m in members]


def delete_team_and_related(team_id):
    """Deletes a team, its members, projects, and related tasks.

    Args:
        team_id (int): ID of the team.

    Returns:
        bool: True if deleted, False if not found.
    """
    projects = Project.query.filter_by(team_id=team_id).all()
    for project in projects:
        Task.query.filter_by(project_id=project.project_id).delete()

    Project.query.filter_by(team_id=team_id).delete()

    UserTeam.query.filter_by(team_id=team_id).delete()
    team = Team.query.get(team_id)
    if team:
        db.session.delete(team)
        db.session.commit()
        return True
    return False

def get_teams(user_id):
    """
    Retrieve all teams a user is in, along with their projects.

    Args:
        user_id (int): ID of the user.

    Returns:
        list: List of dicts containing team and project information.
    """
    user_teams = db.session.query(UserTeam).filter_by(user_id=user_id).join(Team).all()

    result = []
    for ut in user_teams:
        team = ut.team
        projects = Project.query.filter_by(team_id=team.team_id).all()
        result.append(
            {
                "team_id": team.team_id,
                "team_name": team.name,
                "role": ut.role,
                "projects": projects,
            }
        )
    return result
