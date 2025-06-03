# from sqlalchemy import create_engine

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_db(app):
    with app.app_context():
        db.create_all()


class Base(db.Model):
    __abstract__ = True
