import os
from dotenv import load_dotenv

load_dotenv()


basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "default-secret")
    FLASK_ENV = os.getenv("FLASK_ENV", "production")

    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(
        basedir,
        os.getenv("DATABASE_FOLDER", "backend"),
        os.getenv("DATABASE_NAME", "database.db"),
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_EXTENSIONS = os.getenv("UPLOAD_EXTENSIONS", ".jpg,.png").split(",")
    UPLOAD_PATH = os.getenv("UPLOAD_PATH")
    UPLOAD_FOLDER = os.path.join(os.getcwd(), UPLOAD_PATH)

    # Mail
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 465))
    MAIL_USE_SSL = os.getenv("MAIL_USE_SSL", "True") == "True"
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "False") == "True"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")

    # JWT
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "default-jwt-secret")
