from flask_sqlalchemy import SQLAlchemy

# Initialize the SQLAlchemy object globally
# It will later be linked to the Flask app via `init_app`
db = SQLAlchemy()


def init_db(app):
    """Initialize the database by creating all tables.

    Args:
        app (Flask): The Flask application instance.
    """
    with app.app_context():
        db.create_all()


class Base(db.Model):
    """Abstract base class for all SQLAlchemy models."""

    __abstract__ = True
