"""MeridianHR Employee Portal - Vulnerable Flask Application.

WARNING: This application is intentionally vulnerable (CWE-530).
         Backup files with credentials are accessible via the web server.
         DO NOT deploy this in any production environment.
"""

import os

from flask import Flask, request, session, redirect, send_from_directory, render_template_string

app = Flask(__name__)
app.secret_key = "meridian-hr-s3cret-2024"

ADMIN_USER = "hradmin"
ADMIN_PASS = "M3ridian_HR!2024"


# ------------------------------------------------------------------
# VULNERABILITY: Backup files served by web server (CWE-530)
# ------------------------------------------------------------------
@app.route("/config.bak")
def serve_config_backup():
    return send_from_directory("/app", "config.bak", mimetype="text/plain")


@app.route("/settings.old")
def serve_settings_old():
    return send_from_directory("/app", "settings.old", mimetype="text/plain")


@app.route("/.maintenance/<path:filename>")
def serve_maintenance(filename):
    return send_from_directory("/var/www/html/.maintenance", filename)


# ------------------------------------------------------------------
# Main Portal
# ------------------------------------------------------------------
INDEX_HTML = """
<!DOCTYPE html>
<html>
<head><title>MeridianHR - Employee Portal</title>
<style>
body { font-family: 'Segoe UI', sans-serif; margin: 0; background: #f0f2f5; }
.header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px 40px; }
.container { max-width: 800px; margin: 30px auto; padding: 20px; }
.card { background: white; padding: 25px; border-radius: 10px; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
h1 { margin: 0; }
a { color: #667eea; text-decoration: none; }
.nav { margin-top: 10px; }
.nav a { margin-right: 20px; color: rgba(255,255,255,0.8); }
</style>
</head>
<body>
<div class="header">
    <h1>MeridianHR</h1>
    <div class="nav">
        <a href="/">Home</a>
        <a href="/directory">Employee Directory</a>
        <a href="/benefits">Benefits</a>
        <a href="/admin/login">Admin</a>
    </div>
</div>
<div class="container">
    <div class="card">
        <h2>Welcome to the Employee Self-Service Portal</h2>
        <p>Access your payroll information, benefits enrollment, and company directory.</p>
    </div>
    <div class="card">
        <h3>Quick Links</h3>
        <ul>
            <li><a href="/directory">Employee Directory</a></li>
            <li><a href="/benefits">Benefits Information</a></li>
            <li><a href="/payroll">Payroll Portal</a> (coming soon)</li>
        </ul>
    </div>
    <div class="card" style="color: #999; font-size: 0.9em;">
        <p>MeridianHR v2.1.4 | System Status: Online</p>
        <p>Note: System maintenance completed on 2024-01-15. Contact IT if issues persist.</p>
    </div>
</div>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(INDEX_HTML)


@app.route("/directory")
def directory():
    return render_template_string("""
    <!DOCTYPE html><html><head><title>Employee Directory</title>
    <style>body{font-family:sans-serif;margin:40px;} table{border-collapse:collapse;width:100%;} th,td{padding:10px;border:1px solid #ddd;} th{background:#667eea;color:white;}</style>
    </head><body>
    <h2>Employee Directory</h2>
    <table><tr><th>Name</th><th>Department</th><th>Email</th></tr>
    <tr><td>Alice Chen</td><td>Engineering</td><td>alice.chen@meridianhr.local</td></tr>
    <tr><td>Bob Martinez</td><td>Sales</td><td>bob.martinez@meridianhr.local</td></tr>
    <tr><td>Carol White</td><td>HR</td><td>carol.white@meridianhr.local</td></tr>
    <tr><td>David Kim</td><td>Finance</td><td>david.kim@meridianhr.local</td></tr>
    </table>
    <p><a href="/">Back to Home</a></p>
    </body></html>
    """)


@app.route("/benefits")
def benefits():
    return "<h2>Benefits Portal</h2><p>Health, dental, vision plans available.</p><a href='/'>Back</a>"


# ------------------------------------------------------------------
# Admin Panel
# ------------------------------------------------------------------
ADMIN_LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head><title>MeridianHR Admin</title>
<style>
body { font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; background: #f0f2f5; margin: 0; }
.login-box { background: white; padding: 40px; border-radius: 10px; width: 350px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
h2 { color: #667eea; text-align: center; }
input { width: 100%; padding: 10px; margin: 8px 0; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
button { width: 100%; padding: 10px; background: #667eea; color: white; border: none; border-radius: 4px; cursor: pointer; }
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
<head><title>Admin Panel</title>
<style>
body { font-family: sans-serif; margin: 40px; background: #f0f2f5; }
.container { max-width: 800px; margin: auto; }
.card { background: white; padding: 25px; border-radius: 10px; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
.flag-box { background: #e8f5e9; padding: 15px; border-radius: 4px; margin: 10px 0; font-family: monospace; }
a { color: #667eea; }
</style>
</head>
<body>
<div class="container">
    <h1>MeridianHR - Admin Panel</h1>
    <div class="card">
        <h3>User Flag</h3>
        <div class="flag-box">{{ user_flag }}</div>
    </div>
    <div class="card">
        <h3>System Configuration</h3>
        <div class="flag-box">Root Flag: {{ root_flag }}</div>
    </div>
    <p><a href="/">Back to Portal</a> | <a href="/logout">Logout</a></p>
</div>
</body>
</html>
"""


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if session.get("admin"):
        return redirect("/admin/panel")

    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        if username == ADMIN_USER and password == ADMIN_PASS:
            session["admin"] = True
            session["logged_in"] = True
            return redirect("/admin/panel")
        else:
            return render_template_string(ADMIN_LOGIN_HTML, error="Invalid credentials.")

    return render_template_string(ADMIN_LOGIN_HTML, error=None)


@app.route("/admin/panel")
def admin_panel():
    if not session.get("admin"):
        return redirect("/admin/login")

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
        root_flag = "[requires root - check /root/root.txt]"

    return render_template_string(ADMIN_PANEL_HTML, user_flag=user_flag, root_flag=root_flag)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/robots.txt")
def robots():
    return "User-agent: *\nDisallow: /admin/\nDisallow: /.maintenance/\n", 200, {"Content-Type": "text/plain"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
