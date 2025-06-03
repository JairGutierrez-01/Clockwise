from backend.models.team import Team


def test_team_is_valid():
    team = Team(name="Lineare Algebra")
    assert team.is_valid() is True
