"""DevForge Project Manager - Vulnerable Flask Application.

WARNING: This application is intentionally vulnerable (CWE-538).
         The .git directory is exposed and contains secrets in old commits.
         DO NOT deploy this in any production environment.
"""

import os

from flask import Flask, request, session, redirect, send_from_directory, render_template_string, abort

app = Flask(__name__)
app.secret_key = "devforge-super-secret-key-2024"

ADMIN_USER = "devadmin"
ADMIN_PASS = "D3vF0rge_Adm!n2024"

GIT_REPO = "/app/repo"


# ------------------------------------------------------------------
# VULNERABILITY: Exposed .git directory (CWE-538)
# Serves all files from the .git directory
# ------------------------------------------------------------------
@app.route("/.git/<path:filepath>")
def serve_git(filepath):
    """Serve files from the .git directory -- intentional vulnerability."""
    git_dir = os.path.join(GIT_REPO, ".git")
    full_path = os.path.join(git_dir, filepath)

    # Prevent directory traversal
    real_git = os.path.realpath(git_dir)
    real_path = os.path.realpath(full_path)
    if not real_path.startswith(real_git):
        abort(403)

    if os.path.isfile(full_path):
        directory = os.path.dirname(full_path)
        filename = os.path.basename(full_path)
        return send_from_directory(directory, filename, mimetype="application/octet-stream")
    elif os.path.isdir(full_path):
        # List directory contents (helps with git-dumper)
        files = os.listdir(full_path)
        listing = "\n".join(files)
        return listing, 200, {"Content-Type": "text/plain"}
    else:
        abort(404)


@app.route("/.devops/<path:filename>")
def serve_devops(filename):
    return send_from_directory("/var/www/html/.devops", filename)


# ------------------------------------------------------------------
# Main Page
# ------------------------------------------------------------------
INDEX_HTML = """
<!DOCTYPE html>
<html>
<head><title>DevForge - Project Manager</title>
<style>
body { font-family: 'Courier New', monospace; margin: 0; background: #0d1117; color: #c9d1d9; }
.header { background: #161b22; padding: 20px 40px; border-bottom: 1px solid #30363d; }
.header h1 { color: #58a6ff; margin: 0; }
.container { max-width: 900px; margin: 30px auto; padding: 20px; }
.card { background: #161b22; padding: 20px; border-radius: 6px; border: 1px solid #30363d; margin: 15px 0; }
a { color: #58a6ff; }
.project { padding: 10px 0; border-bottom: 1px solid #30363d; }
.tag { background: #1f6feb; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.8em; }
</style>
</head>
<body>
<div class="header">
    <h1>DevForge</h1>
    <p>Internal Project Management</p>
</div>
<div class="container">
    <div class="card">
        <h2>Active Projects</h2>
        <div class="project">
            <strong>Phoenix Backend</strong> <span class="tag">active</span>
            <p>Core API service rewrite - Sprint 14</p>
        </div>
        <div class="project">
            <strong>Atlas Frontend</strong> <span class="tag">active</span>
            <p>React dashboard migration</p>
        </div>
        <div class="project">
            <strong>Sentinel Security</strong> <span class="tag">review</span>
            <p>Security audit tooling</p>
        </div>
    </div>
    <div class="card">
        <h3>Quick Links</h3>
        <ul>
            <li><a href="/status">System Status</a></li>
            <li><a href="/admin">Admin Panel</a></li>
        </ul>
    </div>
    <p style="color: #484f58;">DevForge v2.1.0 | Deployed from git</p>
</div>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(INDEX_HTML)


@app.route("/status")
def status():
    return {"status": "ok", "version": "2.1.0", "uptime": "14d 6h 32m"}


# ------------------------------------------------------------------
# Admin Panel
# ------------------------------------------------------------------
ADMIN_LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head><title>DevForge Admin</title>
<style>
body { font-family: monospace; background: #0d1117; color: #c9d1d9; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
.login-box { background: #161b22; padding: 40px; border-radius: 6px; border: 1px solid #30363d; width: 350px; }
h2 { color: #58a6ff; text-align: center; }
input { width: 100%; padding: 10px; margin: 8px 0; background: #0d1117; border: 1px solid #30363d; color: #c9d1d9; border-radius: 4px; box-sizing: border-box; }
button { width: 100%; padding: 10px; background: #238636; color: white; border: none; border-radius: 4px; cursor: pointer; }
.error { color: #f85149; text-align: center; }
</style>
</head>
<body>
<div class="login-box">
    <h2>Admin Login</h2>
    {% if error %}<p class="error">{{ error }}</p>{% endif %}
    <form method="POST">
        <input type="text" name="username" placeholder="Username" required>
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
<head><title>DevForge Admin</title>
<style>
body { font-family: monospace; background: #0d1117; color: #c9d1d9; margin: 40px; }
.container { max-width: 800px; margin: auto; }
.card { background: #161b22; padding: 20px; border-radius: 6px; border: 1px solid #30363d; margin: 15px 0; }
.flag-box { background: #0d2818; padding: 15px; border-radius: 4px; border: 1px solid #238636; font-family: monospace; margin: 10px 0; }
a { color: #58a6ff; }
</style>
</head>
<body>
<div class="container">
    <h1>DevForge Admin Panel</h1>
    <div class="card">
        <h3>User Flag</h3>
        <div class="flag-box">{{ user_flag }}</div>
    </div>
    <div class="card">
        <h3>System Secrets</h3>
        <div class="flag-box">Root Flag: {{ root_flag }}</div>
    </div>
    <div class="card">
        <h3>Git Info</h3>
        <div class="flag-box">Git Flag: {{ git_flag }}</div>
    </div>
    <p><a href="/">Back</a> | <a href="/logout">Logout</a></p>
</div>
</body>
</html>
"""


@app.route("/admin", methods=["GET", "POST"])
def admin():
    if session.get("admin"):
        user_flag = root_flag = git_flag = "[not accessible]"
        try:
            with open("/home/webapp/user.txt") as f:
                user_flag = f.read().strip()
        except Exception:
            pass
        try:
            with open("/root/root.txt") as f:
                root_flag = f.read().strip()
        except Exception:
            root_flag = "[requires root access]"
        try:
            with open("/opt/devforge/git_flag.txt") as f:
                git_flag = f.read().strip()
        except Exception:
            pass

        return render_template_string(ADMIN_PANEL_HTML,
                                      user_flag=user_flag, root_flag=root_flag, git_flag=git_flag)

    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if username == ADMIN_USER and password == ADMIN_PASS:
            session["admin"] = True
            return redirect("/admin")
        return render_template_string(ADMIN_LOGIN_HTML, error="Invalid credentials.")

    return render_template_string(ADMIN_LOGIN_HTML, error=None)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/robots.txt")
def robots():
    return "User-agent: *\nDisallow: /.git/\nDisallow: /admin/\nDisallow: /.devops/\n", 200, {"Content-Type": "text/plain"}


if __name__ == "__main__":
    # Initialize git repo if not done
    if not os.path.exists(os.path.join(GIT_REPO, ".git")):
        os.system("bash /app/init_git.sh")

    app.run(host="0.0.0.0", port=8080, debug=False)
