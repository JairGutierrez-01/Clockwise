from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("homepage.html")

#@app.route("/login", methods=["GET", "POST"])
#def login():
#    if request.method == "POST":
#       username = request.form.get("username")
#        password = request.form.get("password")
#        # Daten prüfen hier
#        return redirect(url_for("dashboard"))  # Demo access: skip real login for now
#    return render_template("loginpage.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # hier Login Daten prüfen
        return redirect(url_for('dashboard'))
    return render_template('loginpage.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Registrierung verarbeiten
        pass
    return render_template('registerpage.html')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        # E-Mail senden oder Token generieren
        pass
    return render_template('forgotpassword.html')

@app.route("/enter_token", methods=["GET", "POST"])
def enter_token():
    if request.method == "POST":
        token = request.form.get("token")
        # Tokenprüfung hier
    return render_template("enter_token.html")



# Dummy dashboard for prototype
#@app.route("/dashboard")
#def dashboard():
#    return render_template("dashboard.html")  # Dummy dashboard for prototype


# New routes for prototype navigation

@app.route("/TimeTracking")
def timeTracking():
    return ("<h1>Time Tracking page</h1>")
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
    return "<h1>logout page</h1>"

if __name__ == "__main__":
    app.run(debug=True)