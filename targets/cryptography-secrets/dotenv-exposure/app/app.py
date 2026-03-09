"""CloudPulse Analytics Dashboard - Vulnerable Flask Application.

WARNING: This application is intentionally vulnerable (CWE-538).
         The .env file is served by the web server due to misconfiguration.
         DO NOT deploy this in any production environment.
"""

import os

from flask import Flask, request, session, redirect, send_from_directory, render_template_string

app = Flask(__name__)
app.secret_key = "cp-s3cr3t-k3y-x7m9p2q4"

# Admin credentials (loaded from .env in a real app, hardcoded here for the lab)
ADMIN_USER = "cloudadmin"
ADMIN_PASS = "Puls3_@dmin!2024"

# ------------------------------------------------------------------
# VULNERABILITY: Serve files from app root, including .env (CWE-538)
# ------------------------------------------------------------------
@app.route("/.env")
def serve_dotenv():
    """Misconfigured route that serves the .env file directly."""
    return send_from_directory("/app", ".env", mimetype="text/plain")


@app.route("/.backup/<path:filename>")
def serve_backup(filename):
    """Serve backup files -- recon flag lives here."""
    return send_from_directory("/var/www/html/.backup", filename)


# ------------------------------------------------------------------
# Main Page
# ------------------------------------------------------------------
INDEX_HTML = """
<!DOCTYPE html>
<html>
<head><title>CloudPulse Analytics</title>
<style>
body { font-family: 'Segoe UI', sans-serif; margin: 0; background: #1a1a2e; color: #eee; }
.navbar { background: #16213e; padding: 15px 30px; display: flex; justify-content: space-between; }
.navbar h2 { margin: 0; color: #0ea5e9; }
.container { max-width: 900px; margin: 40px auto; padding: 30px; background: #16213e; border-radius: 10px; }
.card { background: #0f3460; padding: 20px; border-radius: 8px; margin: 15px 0; }
.metric { font-size: 2em; color: #0ea5e9; }
a { color: #0ea5e9; }
</style>
</head>
<body>
<div class="navbar">
    <h2>CloudPulse Analytics</h2>
    <span>{% if session.get('logged_in') %}<a href="/admin">Admin</a> | <a href="/logout">Logout</a>{% else %}<a href="/admin">Login</a>{% endif %}</span>
</div>
<div class="container">
    <h1>Dashboard</h1>
    <div class="card">
        <p>Active Users</p>
        <div class="metric">12,847</div>
    </div>
    <div class="card">
        <p>API Requests (24h)</p>
        <div class="metric">2.4M</div>
    </div>
    <div class="card">
        <p>Revenue (MTD)</p>
        <div class="metric">$148,320</div>
    </div>
    <p style="color: #666; margin-top: 30px;">CloudPulse v3.2.1 | &copy; 2024</p>
</div>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(INDEX_HTML)


# ------------------------------------------------------------------
# Admin Panel
# ------------------------------------------------------------------
ADMIN_LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head><title>CloudPulse Admin</title>
<style>
body { font-family: 'Segoe UI', sans-serif; margin: 0; background: #1a1a2e; color: #eee; display: flex; justify-content: center; align-items: center; height: 100vh; }
.login-box { background: #16213e; padding: 40px; border-radius: 10px; width: 350px; }
h2 { color: #0ea5e9; text-align: center; }
input { width: 100%; padding: 10px; margin: 8px 0; border: 1px solid #333; background: #0f3460; color: #eee; border-radius: 4px; box-sizing: border-box; }
button { width: 100%; padding: 10px; background: #0ea5e9; color: white; border: none; border-radius: 4px; cursor: pointer; margin-top: 10px; }
.error { color: #e74c3c; text-align: center; }
</style>
</head>
<body>
<div class="login-box">
    <h2>Admin Login</h2>
    {% if error %}<p class="error">{{ error }}</p>{% endif %}
    <form method="POST">
        <input type="text" name="username" placeholder="Admin Username" required>
        <input type="password" name="password" placeholder="Password" required>
        <button type="submit">Sign In</button>
    </form>
</div>
</body>
</html>
"""

ADMIN_PANEL_HTML = """
<!DOCTYPE html>
<html>
<head><title>CloudPulse Admin Panel</title>
<style>
body { font-family: 'Segoe UI', sans-serif; margin: 0; background: #1a1a2e; color: #eee; }
.navbar { background: #16213e; padding: 15px 30px; display: flex; justify-content: space-between; }
.navbar h2 { margin: 0; color: #e74c3c; }
.container { max-width: 900px; margin: 40px auto; padding: 30px; background: #16213e; border-radius: 10px; }
.flag-box { background: #1a4731; padding: 20px; border-radius: 8px; margin: 20px 0; font-family: monospace; font-size: 1.1em; border: 1px solid #2ecc71; }
.card { background: #0f3460; padding: 20px; border-radius: 8px; margin: 15px 0; }
a { color: #0ea5e9; }
</style>
</head>
<body>
<div class="navbar">
    <h2>Admin Panel</h2>
    <span><a href="/">Dashboard</a> | <a href="/logout">Logout</a></span>
</div>
<div class="container">
    <h1>System Administration</h1>
    <div class="flag-box">User Flag: {{ user_flag }}</div>
    <div class="card">
        <h3>System Secrets</h3>
        <div class="flag-box">Root Flag: {{ root_flag }}</div>
    </div>
    <div class="card">
        <h3>Connected Services</h3>
        <ul>
            <li>PostgreSQL - connected</li>
            <li>Redis - connected</li>
            <li>Stripe API - active</li>
            <li>AWS S3 - configured</li>
        </ul>
    </div>
</div>
</body>
</html>
"""


@app.route("/admin", methods=["GET", "POST"])
def admin():
    if session.get("admin"):
        # Read flags
        user_flag = root_flag = "[not accessible]"
        try:
            with open("/home/webapp/user.txt") as f:
                user_flag = f.read().strip()
        except Exception:
            pass
        try:
            with open("/root/root.txt") as f:
                root_flag = f.read().strip()
        except Exception:
            root_flag = "[requires root access - check /root/root.txt]"

        return render_template_string(ADMIN_PANEL_HTML, user_flag=user_flag, root_flag=root_flag)

    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        if username == ADMIN_USER and password == ADMIN_PASS:
            session["logged_in"] = True
            session["admin"] = True
            return redirect("/admin")
        else:
            return render_template_string(ADMIN_LOGIN_HTML, error="Invalid admin credentials.")

    return render_template_string(ADMIN_LOGIN_HTML, error=None)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/robots.txt")
def robots():
    return "User-agent: *\nDisallow: /admin/\nDisallow: /.backup/\n", 200, {"Content-Type": "text/plain"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
