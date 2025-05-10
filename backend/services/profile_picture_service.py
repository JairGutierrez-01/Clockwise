import os
import uuid

from flask import current_app
from werkzeug.utils import secure_filename


def create_profile_picture(existing_user, profile_picture):
    """
    Saves a new profile picture and deletes the user's old picture if necessary.

    Args:
    existing_user: User object with an existing profile picture.
    profile_picture: File object from a form (e.g., request.files["..."]).

    Returns:
    Path to the saved image (str).
    """
    os.remove(existing_user.profile_picture)
    filename = secure_filename(profile_picture.filename)
    picture_name = str(uuid.uuid1()) + "_" + filename
    filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], picture_name)
    profile_picture.save(filepath)
    return filepath
