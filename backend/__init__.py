"""from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base

DATABASE_URL = "sqlite:///database.db"

engine = create_engine(DATABASE_URL, echo=True, future=True)
SessionLocal = scoped_session(
    sessionmaker(bind=engine, autoflush=False, autocommit=False)
)
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
Base = declarative_base()
"""
