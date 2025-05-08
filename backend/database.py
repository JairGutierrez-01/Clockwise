from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Create a SQLite database connection.
db = create_engine(
    "sqlite:///clockwise.db", echo=True
)  # echo=True for debugging output
"""
Creates an engine that establishes a connection to the SQLite database "clockwise.db".

Args:
    echo (bool): If True, the engine will output SQL queries and results for debugging purposes.

Returns:
    Engine: An SQLAlchemy engine for the database connection.
"""

# SessionLocal is a factory function for creating sessions.
SessionLocal = sessionmaker(bind=db)
"""
Creates a session factory that is bound to the database engine.

Args:
    bind (Engine): The engine to which the session will be bound.

Returns:
    sessionmaker: A session factory used for transactions.
"""

# Base is the base class for declaring ORM models.
Base = declarative_base()
"""
Creates the base class that all ORM classes must inherit from.

Returns:
    Base: A base class for declarative models, used by SQLAlchemy.
"""
