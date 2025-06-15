import os

from dotenv import load_dotenv

load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    """
    Configuration class for Flask application settings.

    Loads environment variables from a .env file and provides
    default values if not set.

    Attributes:
        SECRET_KEY (str): Secret key for session management.
        FLASK_ENV (str): Environment mode ('production', 'development', etc.).
        SQLALCHEMY_DATABASE_URI (str): URI for the database connection.
        SQLALCHEMY_TRACK_MODIFICATIONS (bool): Disable modification tracking.
        UPLOAD_EXTENSIONS (list[str]): Allowed file extensions for uploads.
        UPLOAD_PATH (str): Relative path for upload directory.
        UPLOAD_FOLDER (str): Absolute path for upload directory.
        MAIL_SERVER (str): SMTP mail server hostname.
        MAIL_PORT (int): SMTP mail server port.
        MAIL_USE_SSL (bool): Whether to use SSL for SMTP.
        MAIL_USE_TLS (bool): Whether to use TLS for SMTP.
        MAIL_USERNAME (str): Username for SMTP authentication.
        MAIL_PASSWORD (str): Password for SMTP authentication.
        JWT_SECRET_KEY (str): Secret key used for JWT encoding/decoding.
    """

    SECRET_KEY = os.getenv("SECRET_KEY", "default-secret")
    FLASK_ENV = os.getenv("FLASK_ENV", "production")

    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(
        basedir,
        os.getenv("DATABASE_FOLDER", "backend"),
        os.getenv("DATABASE_NAME", "database.db"),
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_EXTENSIONS = os.getenv("UPLOAD_EXTENSIONS", ".jpg,.png").split(",")
    UPLOAD_PATH = os.getenv("UPLOAD_PATH", "uploads")
    UPLOAD_FOLDER = os.path.join(os.getcwd(), UPLOAD_PATH)

    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 465))
    MAIL_USE_SSL = os.getenv("MAIL_USE_SSL", "True").lower() in ("true", "1", "yes")
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "False").lower() in ("true", "1", "yes")
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "default-jwt-secret")
