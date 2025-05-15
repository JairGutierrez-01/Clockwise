import os
import uuid

from flask import current_app
from werkzeug.utils import secure_filename


def create_profile_picture(existing_user, profile_picture):
    """
    Saves a new profile picture and deletes the user's old picture if necessary.

    Args:
    existing_user: User object with an existing profile picture, or None.
    profile_picture: File object from a form (e.g., request.files["..."]).

    Returns:
    Relative path to the saved image (str), e.g., "profile_pictures/xyz.png"
    """
    if existing_user and existing_user.profile_picture:
        old_path = os.path.join(current_app.static_folder, existing_user.profile_picture)
        if os.path.exists(old_path):
            os.remove(old_path)

    filename = secure_filename(profile_picture.filename)
    picture_name = f"{uuid.uuid4()}_{filename}"
    relative_path = os.path.join("profile_pictures", picture_name)
    full_path = os.path.join(current_app.static_folder, relative_path)

    profile_picture.save(full_path)
    return relative_path
