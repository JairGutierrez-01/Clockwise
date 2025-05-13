from backend.models.team import Team
from backend.models.project import Project
from backend.models.user_team import UserTeam
from backend.models.user import User
from backend.models.notification import Notification
from backend.models.task import Task
from backend.models.time_entry import TimeEntry
from backend.models.category import Category


def test_team_is_valid():
    team = Team(name="Lineare Algebra")
    assert team.is_valid() is True
