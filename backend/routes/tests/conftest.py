import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from app import app

from sqlalchemy.orm import sessionmaker, scoped_session
from backend.database import db  # Stelle sicher, dass dein db Objekt von dort kommt

import pytest


@pytest.fixture()
def db_session(flask_app):
    connection = db.engine.connect()
    transaction = connection.begin()

    session_factory = sessionmaker(bind=connection)
    session = scoped_session(session_factory)

    db.session = session  # setzt globale Session für App

    yield session

    transaction.rollback()
    connection.close()
    session.remove()


@pytest.fixture()
def flask_app():
    app.config.update(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        }
    )

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture()
def client(flask_app):
    return flask_app.test_client()


@pytest.fixture()
def runner(flask_app):
    return flask_app.test_cli_runner()
