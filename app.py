import os
from datetime import datetime, timedelta

from dotenv import load_dotenv
from flask import Flask, render_template, redirect, url_for
from flask import jsonify
from flask import request
from flask_jwt_extended import JWTManager
from flask_login import LoginManager, login_user, logout_user
from flask_login import current_user
from flask_login import login_required
from flask_mail import Mail
from flask_migrate import Migrate
from sqlalchemy import select

from backend.database import db
from backend.models import UserTeam
from backend.models.notification import Notification
from backend.models.project import Project
from backend.models.user import User
from backend.routes.analysis_routes import analysis_bp
from backend.routes.category_routes import category_bp
from backend.routes.notification_routes import notification_bp
from backend.routes.project_routes import project_bp
from backend.routes.task_routes import task_bp
from backend.routes.team_routes import team_bp
from backend.routes.time_entry_routes import time_entry_bp
from backend.routes.user_routes import auth_bp
from backend.services.analysis_service import calendar_due_dates, calendar_worked_time
from backend.services.task_service import get_task_by_id
from backend.services.team_service import get_teams
from backend.services.time_entry_service import get_time_entries_by_task

"""
Main Flask application module for the backend API and frontend rendering.

This module initializes the Flask app, loads configuration from environment variables,
registers blueprints for modular route handling, and sets up extensions such as SQLAlchemy,
Flask-Migrate, Flask-Mail, Flask-Login, and Flask-JWT-Extended.

Routes include user authentication (login/logout), project and team views, time tracking,
notifications, and various API endpoints for analysis, categories, tasks, time entries, and more.

Key Features:
- Environment configuration loading via python-dotenv
- SQLAlchemy ORM for database interaction with migrations support
- User session management and authentication with Flask-Login and JWT
- Modular route structure via Blueprints
- Template rendering for frontend pages with static asset cache busting
- Notification management including reading, deleting, and test notifications
- JSON APIs for calendar data and analysis services
- Secure file upload folder initialization

Usage:
    Run this module directly to start the Flask development server:

        python app.py

    Or use a production WSGI server pointing to `app` Flask instance.

Modules and Blueprints:
- `auth_bp`: User authentication routes (login, logout, register)
- `team_bp`: Team-related API endpoints
- `notification_bp`: Notification management endpoints
- `task_bp`: Task API endpoints
- `time_entry_bp`: Time entry management API
- `project_bp`: Project views and APIs
- `category_bp`: Category management API
- `analysis_bp`: Data analysis endpoints (calendar views, reports)

Template Context Processors:
- `override_url_for`: Adds cache-busting query parameter to static file URLs
- `inject_user_status`: Injects user login status and unread notification flag

Flask-Login User Loader:
- Loads a user by user ID for session management

Example routes:
- `/login`: User login page and submission
- `/dashboard`: Main user dashboard page
- `/projects`: List of user and team projects
- `/notifications`: List and management of user notifications
- `/calendar-due-dates`: API returning due dates for calendar visualization
- `/time_entries`: Time entry page for specific tasks
"""

# Load environment variables from .env file
load_dotenv()

app = Flask(
    __name__, template_folder="frontend/templates", static_folder="frontend/static"
)

# Load configuration from config.py
app.config.from_object("config.Config")

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)
mail = Mail(app)
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.init_app(app)
jwt = JWTManager(app)

# Create an upload folder if not exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Register Blueprints
app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(team_bp, url_prefix="/api/teams")

app.register_blueprint(notification_bp, url_prefix="/notifications")
app.register_blueprint(task_bp, url_prefix="/api")
app.register_blueprint(time_entry_bp, url_prefix="/api/time_entries")
# For HTML Tempaltes
app.register_blueprint(project_bp)
# For API-Zugriffe
app.register_blueprint(project_bp, url_prefix="/api/projects", name="project_api")
app.register_blueprint(category_bp)
app.register_blueprint(analysis_bp, url_prefix="/api/analysis")
# Create tables if not exist
with app.app_context():
    db.create_all()

# Secret key is now in config.py loaded from .env


@app.context_processor
def override_url_for():
    """
    Context processor to add cache-busting query parameter to static file URLs.

    This helps force the browser to reload static files (like CSS/JS/images)
    when they change, by appending a timestamp based on the file's last modification time.

    Returns:
        dict: A dictionary with a custom 'url_for' function to use in Jinja2 templates.
    """

    def dated_url_for(endpoint, **values):
        if endpoint == "static":
            filename = values.get("filename", None)
            if filename:
                file_path = os.path.join(app.static_folder, filename)
                if os.path.exists(file_path):
                    values["v"] = int(os.stat(file_path).st_mtime)
        return url_for(endpoint, **values)

    return dict(url_for=dated_url_for)


@app.route("/")
def home():
    """
    Render the homepage.

    Returns:
        str: Rendered HTML template for the homepage.
    """
    return render_template("homepage.html")


@app.route("/ping", methods=["POST"])
@login_required
def ping():
    """
    Update the current user's last active timestamp to the current time.

    This endpoint is intended to be called periodically to mark the user as active.

    Returns:
        tuple: An empty response with HTTP status code 204 (No Content).
    """
    now = datetime.now()
    current_user.last_active = now
    db.session.commit()
    return "", 204


@app.route("/calendar-due-dates")
@login_required
def get_calendar_due_dates():
    """
    API endpoint to return calendar due dates as JSON.

    Requires user to be logged in.

    Returns:
        Response: JSON response containing due dates data.
    """
    return jsonify(calendar_due_dates())


@app.route("/login", methods=["GET", "POST"])
def login():
    """
    User login endpoint. Handles GET and POST requests.

    GET: Render login page.
    POST: Authenticate user with username and password.
          On success, log in the user and redirect to dashboard.
          On failure, show login page with error message.

    Returns:
        str or Response: Rendered template or redirect response.
    """
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()

        if user and user.password == password:
            login_user(user)
            return redirect(url_for("dashboard"))
        else:
            return render_template("loginpage.html", error="Invalid credentials")

    return render_template("loginpage.html")


@app.route("/dashboard")
def dashboard():
    """
    Render the main dashboard page.

    Returns:
        str: Rendered HTML template for the dashboard.
    """
    return render_template("dashboard.html")


@app.route("/TimeTracking")
@login_required
def timeTracking():
    """
    Render the time tracking page.

    Requires user login.

    Returns:
        str: Rendered HTML template for time tracking.
    """
    return render_template("timeTracking.html")


@app.route("/analysis")
@login_required
def analysis():
    """
    Render the analysis page showing reports and charts.

    Requires user login.

    Returns:
        str: Rendered HTML template for analysis.
    """

    return render_template("analysis.html")


@app.route("/projects", methods=["GET", "POST"])
@login_required
def projects():
    """
    Display a list of projects for the current user.

    Fetches projects directly owned by the user and those linked to user's teams.
    Combines results and renders the projects page.

    Returns:
        str: Rendered HTML template with user's projects.
    """
    if not current_user.is_authenticated:
        return redirect(url_for("login"))

    team_id_select = (
        select(UserTeam.team_id)
        .where(UserTeam.user_id == current_user.user_id)
        .subquery()
    )
    user_q = Project.query.filter(Project.user_id == current_user.user_id)
    team_q = Project.query.filter(Project.team_id.in_(team_id_select))

    all_projects = user_q.union(team_q).all()
    print("Alle Projekte:", all_projects)
    return render_template("projects.html", projects=all_projects)


@app.route("/teams")
@login_required
def teams():
    """
    Display teams associated with the current user, including their projects.

    Returns:
        str: Rendered HTML template showing user's teams.
    """
    teams = get_teams(current_user.user_id)
    return render_template("teams.html", teams=teams)


@app.route("/logout", methods=["GET", "POST"])
def logout():
    """
    Log out the current user.

    Supports GET and POST requests.
    On POST, returns JSON success message.
    On GET, redirects to homepage.

    Returns:
        Response or str: JSON response or redirect.
    """
    logout_user()

    if request.method == "POST":
        return jsonify({"success": True}), 200

    return redirect(url_for("home"))


"""
@app.route("/logout", methods=["POST"])
def logout():
    logout_user()
    return "", 204
"""


@app.context_processor
def inject_user_status():
    """
    Inject user login status and notification status into templates.

    Checks if current user is authenticated and has unread notifications.

    Returns:
        dict: Contains flags 'user_logged_in' and 'has_notifications'.
    """
    has_unread = False
    if current_user.is_authenticated:
        has_unread = (
            Notification.query.filter_by(
                user_id=current_user.user_id, is_read=False
            ).count()
            > 0
        )

    return dict(
        user_logged_in=current_user.is_authenticated, has_notifications=has_unread
    )


@login_manager.user_loader
def load_user(user_id):
    """
    Flask-Login user loader callback.

    Loads and returns the User object by user_id.

    Args:
        user_id (str or int): User ID from the session.

    Returns:
        User or None: User instance if found, else None.
    """
    return User.query.get(int(user_id))


@app.route("/notifications")
@login_required
def notifications():
    """
    Display the logged-in user's notifications.

    Notifications are ordered by creation date descending.

    Returns:
        str: Rendered HTML template with notifications list.
    """
    if not current_user.is_authenticated:
        return redirect(url_for("login"))

    user_notifications = (
        Notification.query.filter_by(user_id=current_user.user_id)
        .order_by(Notification.created_at.desc())
        .all()
    )
    return render_template("notifications.html", notifications=user_notifications)


# Test notification erstellen
@app.route("/notifications/trigger-test-notification")
@login_required
def trigger_test_notification():
    """
    Create a test notification for the current user.

    Useful for testing notification system.

    Returns:
        Response: Redirect to notifications page.
    """
    if not current_user.is_authenticated:
        return "Not logged in", 403

    from backend.services.notifications import create_notification

    create_notification(
        user_id=current_user.user_id,
        message="🎉 Testbenachrichtigung erfolgreich erstellt!",
        notif_type="info",
    )
    return redirect(url_for("notifications"))


@app.route("/time_entries")
@login_required
def time_entry_page():
    """
    Render time entries page for a specific task.

    Expects query parameter 'id' for task ID.

    Args:
        id (int, query param): Task ID.

    Returns:
        str: Rendered HTML template showing time entries for the task.
    """
    task_id = int(request.args.get("id"))
    task = get_task_by_id(task_id)
    task_title = task.title if task else "Unbekannte Aufgabe"
    time_entries = get_time_entries_by_task(task_id)
    return render_template(
        "time_entries.html",
        task_id=task_id,
        task_title=task_title,
        time_entries=time_entries,
    )


@app.route("/calendar-worked-time")
@login_required
def get_calendar_worked_time():
    """
    API endpoint to return calendar worked time data as JSON.

    Requires user login.

    Returns:
        Response: JSON response containing worked time data.
    """
    return jsonify(calendar_worked_time())


@app.before_request
def update_last_active():
    if current_user.is_authenticated:
        now = datetime.utcnow()
        if not current_user.last_active or now - current_user.last_active > timedelta(
            minutes=1
        ):
            current_user.last_active = now
            db.session.commit()


if __name__ == "__main__":
    app.run(debug=True)
