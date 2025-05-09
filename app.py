import os
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy

# from backend.models import User, Project
from sqlalchemy.sql import func

# from backend import db
from backend.database import db


from backend.routes.user_routes import auth_bp

app = Flask(
    __name__, template_folder="frontend/templates", static_folder="frontend/static"
)
#####
basedir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "backend")

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(
    basedir, "database.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# TODO: profile picture
app.config["UPLOAD_EXTENSIONS"] = [".jpg", ".png"]
app.config["UPLOAD_PATH"] = "backend/models/profile_pictures"

app.register_blueprint(auth_bp, url_prefix="/auth")

db.init_app(app)
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


# @app.route("/login", methods=["GET", "POST"])
# def login():
#    if request.method == "POST":
#       username = request.form.get("username")
#        password = request.form.get("password")
#        # Daten prüfen hier
#        return redirect(url_for("dashboard"))  # Demo access: skip real login for now
#    return render_template("loginpage.html")

# @app.route('/login', methods=['GET', 'POST'])
# def login():
#   if request.method == 'POST':
# hier Login Daten prüfen
#      session['user_id'] = 'demo_user'  # <- Benutzer als eingeloggt markieren
#     return redirect(url_for('dashboard'))
# return render_template('loginpage.html')


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


"""
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Registrierung verarbeiten
        pass
    return render_template('registerpage.html')
    """


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        # E-Mail senden oder Token generieren
        pass
    return render_template("forgotpassword.html")


@app.route("/enter_token", methods=["GET", "POST"])
def enter_token():
    if request.method == "POST":
        token = request.form.get("token")
        # Tokenprüfung hier
    return render_template("enter_token.html")


# Dummy dashboard for prototype
# @app.route("/dashboard")
# def dashboard():
#    return render_template("dashboard.html")  # Dummy dashboard for prototype


# New routes for prototype navigation


@app.route("/TimeTracking")
def timeTracking():
    return render_template("timeTracking.html")


@app.route("/analysis")
def analysis():
    return "<h1>Analysis page</h1>"


@app.route("/projects")
def projects():
    return "<h1>Projects page</h1>"


@app.route("/teams")
def teams():
    return "<h1>Teams page</h1>"


@app.route("/profile")
def profile():
    return "<h1>Profile page</h1>"


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("home"))


@app.context_processor
def inject_user_status():
    return dict(user_logged_in=session.get("user_id") is not None)


if __name__ == "__main__":
    # from livereload import Server
    # server = Server(app.wsgi_app)
    # server.serve(debug=True)
    app.run(debug=True)
