import os
from unittest.mock import patch

from backend.services.profile_picture_service import create_profile_picture


class DummyFile:
    """A dummy file-like object to simulate an uploaded profile picture."""

    def __init__(self, filename):
        """
        Args:
            filename (str): The name of the dummy file.
        """
        self.filename = filename
        self.saved_path = None

    def save(self, path):
        """Simulate saving the file to disk.

        Args:
            path (str): The full path where the file should be saved.
        """
        self.saved_path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write("dummy image content")


def test_create_profile_picture_new_file(app):
    """Test creating a new profile picture without an existing one.

    Ensures the file is saved in the correct location and the returned path
    starts with 'profile_pictures/'.

    Args:
        app (Flask): The Flask test app fixture with an active app context.
    """
    profile_picture = DummyFile("myphoto.png")

    with app.app_context():
        result_path = create_profile_picture(None, profile_picture)

    assert result_path.replace("\\", "/").startswith("profile_pictures/")
    assert os.path.exists(profile_picture.saved_path)


def test_create_profile_picture_replaces_old_file(app, tmp_path):
    """Test replacing an existing profile picture with a new one.

    Ensures the old file is removed and the new file is saved correctly.

    Args:
        app (Flask): The Flask test app fixture with an active app context.
        tmp_path (Path): Pytest's temporary path fixture for isolated file I/O.
    """
    old_filename = "oldpic.png"
    old_folder = os.path.join(app.static_folder, "profile_pictures")
    os.makedirs(old_folder, exist_ok=True)
    old_path = os.path.join(old_folder, old_filename)

    with open(old_path, "w") as f:
        f.write("old image")

    class ExistingUser:
        profile_picture = os.path.join("profile_pictures", old_filename)

    profile_picture = DummyFile("newphoto.jpg")

    with patch("os.remove") as mock_remove:
        with app.app_context():
            result_path = create_profile_picture(ExistingUser(), profile_picture)
        mock_remove.assert_called_once_with(old_path)

    assert result_path.replace("\\", "/").startswith("profile_pictures/")
    assert os.path.exists(profile_picture.saved_path)
