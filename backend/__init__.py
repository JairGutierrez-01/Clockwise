"""from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app(test_config=None):
    app = Flask(__name__)

    app.config.from_mapping(
        {
            "SECRET_KEY": "dev",
            "SQLALCHEMY_DATABASE_URI": (
                "sqlite:///:memory:" if test_config else "sqlite:///database.db"
            ),
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        }
    )

    if test_config:
        app.config.update(test_config)

    db.init_app(app)

    from backend.routes.user_routes import auth_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")

    with app.app_context():
        db.create_all()

    return app
"""
