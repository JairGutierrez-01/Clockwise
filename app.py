import os

from dotenv import load_dotenv
from flask import Flask, render_template, redirect, url_for
from flask import request
from flask import jsonify
from flask_jwt_extended import JWTManager
from flask_login import LoginManager, login_user, logout_user
from flask_login import current_user
from flask_login import login_required
from flask_mail import Mail
from flask_migrate import Migrate
from sqlalchemy import select, literal

from backend.database import db
from backend.models import UserTeam, Team, Project
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
from backend.services.task_service import get_task_by_id
from backend.services.time_entry_service import get_time_entries_by_task
from backend.services.analysis_service import calendar_due_dates, calendar_worked_time


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

# Create upload folder if not exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Register Blueprints
app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(team_bp, url_prefix="/api/teams")

app.register_blueprint(notification_bp, url_prefix="/api/notifications")
app.register_blueprint(task_bp, url_prefix="/api")
app.register_blueprint(time_entry_bp, url_prefix="/api/time_entries")
# For HTML Tempaltes
app.register_blueprint(project_bp)
# For API-Zugriffe
app.register_blueprint(project_bp, url_prefix="/api/projects", name="project_api")
app.register_blueprint(category_bp, url_prefix="/categories")
app.register_blueprint(analysis_bp, url_prefix="/api/analysis")

# Create tables if not exist
with app.app_context():
    db.create_all()

# Secret key is now in config.py loaded from .env


@app.context_processor
def override_url_for():
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
    return render_template("homepage.html")

@app.route("/calendar-due-dates")
def get_calendar_due_dates():
    return jsonify(calendar_due_dates())

@app.route("/login", methods=["GET", "POST"])
def login():
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
    return render_template("dashboard.html")


@app.route("/TimeTracking")
def timeTracking():
    return render_template("timeTracking.html")


@app.route("/analysis")
def analysis():
    return render_template("analysis.html")


@app.route("/projects", methods=["GET", "POST"])
def projects():
    if not current_user.is_authenticated:
        return redirect(url_for("login"))
    user_projects = Project.query.filter_by(user_id=current_user.user_id).all()
    team_id_select = (
        select(UserTeam.team_id)
        .where(UserTeam.user_id == literal(current_user.user_id))
        .scalar_subquery()
    )
    team_projects = Project.query.filter(Project.team_id.in_(team_id_select)).all()
    all_projects = user_projects + team_projects
    print("Eigene Projekte:", user_projects)
    print("Teamprojekte:", team_projects)
    return render_template("projects.html", projects=all_projects)


@app.route("/teams")
@login_required
def teams():
    user_id = current_user.user_id

    user_teams = (
        db.session.query(UserTeam)
        .filter_by(user_id=user_id)
        .join(Team)
        .all()
    )

    teams_with_projects = []
    for ut in user_teams:
        team = ut.team
        projects = Project.query.filter_by(team_id=UserTeam.team_id).all()
        teams_with_projects.append({
            "team_id": team.team_id,
            "team_name": team.name,
            "role": ut.role,
            "projects": projects,
        })

    return render_template("teams.html", teams=teams_with_projects)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("home"))


@app.context_processor
def inject_user_status():
    return dict(user_logged_in=current_user.is_authenticated, has_notifications=False)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/notifications")
def notifications():
    if not current_user.is_authenticated:
        return redirect(url_for("login"))

    user_notifications = (
        Notification.query.filter_by(user_id=current_user.user_id)
        .order_by(Notification.created_at.desc())
        .all()
    )
    return render_template("notifications.html", notifications=user_notifications)


@app.route("/notifications/delete/<int:notification_id>", methods=["POST"])
def delete_notification(notification_id):
    if not current_user.is_authenticated:
        return "", 403

    notification = Notification.query.get(notification_id)
    if notification and notification.user_id == current_user.user_id:  # <- Fix hier
        db.session.delete(notification)
        db.session.commit()
        return "", 200
    return "", 404

@app.route("/notifications/read/<int:notification_id>", methods=["POST"])
def mark_notification_as_read(notification_id):
    if not current_user.is_authenticated:
        return jsonify({"error": "Not logged in"}), 403

    notification = Notification.query.get(notification_id)
    if not notification or notification.user_id != current_user.user_id:
        return jsonify({"error": "No Messags found"}), 404

    if notification.is_read:
        return jsonify({"message": "Already marked as read"}), 200

    notification.is_read = True
    db.session.commit()
    return jsonify({"message": "Message marked as read"}), 200


# Test notification erstellen
@app.route("/trigger-test-notification")
def trigger_test_notification():
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
def time_entry_page():
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
def get_calendar_worked_time():
    return jsonify(calendar_worked_time())


if __name__ == "__main__":
    app.run(debug=True)
