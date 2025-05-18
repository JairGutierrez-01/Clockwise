import os

from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager
from flask_login import current_user
from flask_login import login_user
from flask_login import logout_user
from flask_mail import Mail
from flask_migrate import Migrate

from backend.database import db
from backend.models.notification import Notification
from backend.models.user import User
from backend.models.project import Project
from backend.routes.notification_routes import notification_bp
from backend.routes.team_routes import team_bp
from backend.routes.user_routes import auth_bp
from backend.routes.task_routes import task_bp
from backend.routes.time_entry_routes import time_entry_bp
from backend.routes.project_routes import project_bp
from backend.routes.category_routes import category_bp

app = Flask(
    __name__, template_folder="frontend/templates", static_folder="frontend/static"
)
login_manager = LoginManager()
login_manager.login_view = "auth.login"  # where to redirect when not logged in
login_manager.init_app(app)

migrate = Migrate(app, db)

#####
basedir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "backend")

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(
    basedir, "database.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.config["UPLOAD_EXTENSIONS"] = [".jpg", ".png"]
app.config["UPLOAD_PATH"] = "frontend/static/profile_pictures"
app.config["UPLOAD_FOLDER"] = os.path.join(os.getcwd(), app.config["UPLOAD_PATH"])
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 465
app.config["MAIL_USE_SSL"] = True
app.config["MAIL_USE_TLS"] = False
app.config["MAIL_USERNAME"] = "sep.clockwise@gmail.com"
app.config["MAIL_PASSWORD"] = "sclpdlhelcwwobob"
mail = Mail(app)
app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(team_bp, url_prefix="/teams")
app.register_blueprint(notification_bp, url_prefix="/api/notifications")
app.register_blueprint(task_bp, url_prefix="/tasks")
app.register_blueprint(time_entry_bp, url_prefix="/api/time_entries")
app.register_blueprint(project_bp)
app.register_blueprint(category_bp, url_prefix="/categories")

db.init_app(app)
from flask_jwt_extended import JWTManager

jwt = JWTManager(app)
with app.app_context():
    db.create_all()

####
app.secret_key = "u89234h2v98vn34vvj2934hvjwef"  # Sicherer zufälliger Key um zu simulieren, dass ein user eingeloggt ist


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


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()

        if user and user.password == password:
            login_user(user)  # ← Das ist entscheidend!
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
    user_projects = Project.query.filter_by(user_id=current_user.user_id).all()
    return render_template("projects.html", projects=user_projects)


@app.route("/teams")
def teams():
    return render_template("teams.html")


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("home"))


# @app.context_processor
# def inject_user_status():
#    return dict(user_logged_in=session.get("user_id") is not None)
# from backend.models import User


@app.context_processor
def inject_user_status():
    return dict(user_logged_in=current_user.is_authenticated, has_notifications=False)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/notifications")
def notifications():
    return render_template("notifications.html")


@app.route("/notifications/delete/<int:notification_id>", methods=["POST"])
def delete_notification(notification_id):
    if not current_user.is_authenticated:
        return "", 403

    notification = Notification.query.get(notification_id)
    if notification and notification.user_id == current_user.id:
        db.session.delete(notification)
        db.session.commit()
        return "", 200
    return "", 404


if __name__ == "__main__":
    # from livereload import Server
    # server = Server(app.wsgi_app)
    # server.serve(debug=True)
    app.run(debug=True)
