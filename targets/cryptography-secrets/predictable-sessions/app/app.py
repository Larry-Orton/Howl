"""QuickBoard Project Dashboard - Vulnerable Flask Application.

WARNING: This application is intentionally vulnerable (CWE-330).
         It uses predictable session token generation.
         DO NOT deploy this in any production environment.
"""

import hashlib
import os
import sqlite3
import time

from flask import Flask, request, redirect, jsonify, render_template_string, make_response, send_from_directory

app = Flask(__name__)

DATABASE = "/app/data/quickboard.db"

# Record the startup timestamp -- this is used in token generation
# and also leaked via the /api/status endpoint
STARTUP_TIME = str(int(time.time()))


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def generate_token(user_id, timestamp):
    """VULNERABLE: Predictable token generation (CWE-330).
    Token = MD5(user_id + ':' + timestamp)
    This is deterministic and guessable.
    """
    token_input = f"{user_id}:{timestamp}"
    return hashlib.md5(token_input.encode()).hexdigest()


def get_user_by_token(token):
    """Look up a user by their session token."""
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE session_token=?", (token,)).fetchone()
    db.close()
    return user


def init_db():
    """Initialize the database."""
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            session_token TEXT,
            created_at TEXT
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            owner TEXT
        )
    """)

    # Create admin user with predictable token
    existing = db.execute("SELECT id FROM users WHERE username='admin'").fetchone()
    if not existing:
        admin_token = generate_token(1, STARTUP_TIME)
        db.execute(
            "INSERT INTO users (username, password, role, session_token, created_at) VALUES (?, ?, ?, ?, ?)",
            ("admin", "Qu1ckB0@rd_Adm!n", "admin", admin_token, STARTUP_TIME),
        )
        db.execute(
            "INSERT INTO projects (name, status, owner) VALUES (?, ?, ?)",
            ("Phoenix Rewrite", "active", "admin"),
        )
        db.execute(
            "INSERT INTO projects (name, status, owner) VALUES (?, ?, ?)",
            ("Mobile App v2", "planning", "admin"),
        )
        db.execute(
            "INSERT INTO projects (name, status, owner) VALUES (?, ?, ?)",
            ("Security Audit", "review", "admin"),
        )

    db.commit()
    db.close()


# ------------------------------------------------------------------
# Main Page
# ------------------------------------------------------------------
INDEX_HTML = """
<!DOCTYPE html>
<html>
<head><title>QuickBoard</title>
<style>
body { font-family: 'Segoe UI', sans-serif; margin: 0; background: #fafafa; }
.navbar { background: #6366f1; color: white; padding: 15px 30px; }
.navbar h2 { margin: 0; }
.container { max-width: 800px; margin: 30px auto; padding: 20px; }
.card { background: white; padding: 25px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin: 15px 0; }
a { color: #6366f1; }
input { padding: 10px; margin: 5px 0; border: 1px solid #ddd; border-radius: 4px; width: 100%; box-sizing: border-box; }
button { padding: 10px 20px; background: #6366f1; color: white; border: none; border-radius: 4px; cursor: pointer; width: 100%; }
.error { color: #ef4444; }
.success { color: #22c55e; }
.token-info { background: #f1f5f9; padding: 10px; border-radius: 4px; font-family: monospace; font-size: 0.85em; word-break: break-all; }
</style>
</head>
<body>
<div class="navbar"><h2>QuickBoard</h2></div>
<div class="container">
    {% if user %}
    <div class="card">
        <h2>Welcome, {{ user.username }}</h2>
        <p>Role: {{ user.role }}</p>
        <p>Your session token:</p>
        <div class="token-info">{{ token }}</div>
        {% if user_flag %}<div class="card" style="background:#f0fdf4;"><strong>User Flag:</strong> {{ user_flag }}</div>{% endif %}
        <p><a href="/projects">My Projects</a> | {% if user.role == 'admin' %}<a href="/admin">Admin Panel</a> | {% endif %}<a href="/logout">Logout</a></p>
    </div>
    {% else %}
    <div class="card">
        <h2>Login</h2>
        {% if error %}<p class="error">{{ error }}</p>{% endif %}
        <form method="POST" action="/login">
            <input type="text" name="username" placeholder="Username" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Login</button>
        </form>
    </div>
    <div class="card">
        <h2>Register</h2>
        {% if reg_msg %}<p class="success">{{ reg_msg }}</p>{% endif %}
        <form method="POST" action="/register">
            <input type="text" name="username" placeholder="Username" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Register</button>
        </form>
    </div>
    {% endif %}
</div>
</body>
</html>
"""


@app.route("/")
def index():
    token = request.cookies.get("session_token")
    user = get_user_by_token(token) if token else None

    user_flag = None
    if user:
        try:
            with open("/home/webapp/user.txt") as f:
                user_flag = f.read().strip()
        except Exception:
            pass

    return render_template_string(INDEX_HTML, user=user, token=token, user_flag=user_flag, error=None, reg_msg=None)


@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username", "")
    password = request.form.get("password", "")

    db = get_db()
    user = db.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password)).fetchone()
    db.close()

    if user:
        # Generate predictable token
        token = generate_token(user["id"], STARTUP_TIME)

        # Update stored token
        db = get_db()
        db.execute("UPDATE users SET session_token=? WHERE id=?", (token, user["id"]))
        db.commit()
        db.close()

        resp = make_response(redirect("/"))
        resp.set_cookie("session_token", token)
        return resp
    else:
        return render_template_string(INDEX_HTML, user=None, token=None, user_flag=None,
                                      error="Invalid credentials.", reg_msg=None)


@app.route("/register", methods=["POST"])
def register():
    username = request.form.get("username", "")
    password = request.form.get("password", "")

    try:
        db = get_db()
        db.execute("INSERT INTO users (username, password, role, created_at) VALUES (?, ?, 'user', ?)",
                   (username, password, str(int(time.time()))))
        db.commit()

        # Get the new user's ID and generate token
        user = db.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone()
        token = generate_token(user["id"], STARTUP_TIME)
        db.execute("UPDATE users SET session_token=? WHERE id=?", (token, user["id"]))
        db.commit()
        db.close()

        resp = make_response(redirect("/"))
        resp.set_cookie("session_token", token)
        return resp
    except sqlite3.IntegrityError:
        return render_template_string(INDEX_HTML, user=None, token=None, user_flag=None,
                                      error=None, reg_msg="Username already taken.")


@app.route("/projects")
def projects():
    token = request.cookies.get("session_token")
    user = get_user_by_token(token) if token else None
    if not user:
        return redirect("/")

    db = get_db()
    projects = db.execute("SELECT * FROM projects WHERE owner=?", (user["username"],)).fetchall()
    db.close()

    rows = ""
    for p in projects:
        rows += f"<tr><td>{p['name']}</td><td>{p['status']}</td></tr>"

    return render_template_string(f"""
    <!DOCTYPE html><html><head><title>Projects</title>
    <style>body{{font-family:sans-serif;margin:40px;}} table{{border-collapse:collapse;width:100%;}}
    th,td{{padding:10px;border:1px solid #ddd;}} th{{background:#6366f1;color:white;}} a{{color:#6366f1;}}</style>
    </head><body><h2>My Projects</h2>
    <table><tr><th>Name</th><th>Status</th></tr>{rows}</table>
    <p><a href="/">Back</a></p></body></html>
    """)


# ------------------------------------------------------------------
# VULNERABILITY: Status endpoint leaks startup timestamp (CWE-200)
# ------------------------------------------------------------------
@app.route("/api/status")
def api_status():
    """Status endpoint that leaks the startup timestamp used in token generation."""
    return jsonify({
        "status": "online",
        "version": "1.4.2",
        "uptime_since": STARTUP_TIME,
        "total_users": get_db().execute("SELECT COUNT(*) FROM users").fetchone()[0],
        "environment": "production",
    })


# ------------------------------------------------------------------
# Admin Panel
# ------------------------------------------------------------------
ADMIN_HTML = """
<!DOCTYPE html>
<html>
<head><title>Admin Panel</title>
<style>
body { font-family: sans-serif; margin: 40px; background: #fafafa; }
.container { max-width: 800px; margin: auto; }
.card { background: white; padding: 25px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin: 15px 0; }
.flag-box { background: #f0fdf4; padding: 15px; border-radius: 4px; border: 1px solid #22c55e; font-family: monospace; margin: 10px 0; }
a { color: #6366f1; }
</style>
</head>
<body>
<div class="container">
    <h1>QuickBoard Admin Panel</h1>
    <div class="card">
        <h3>User Flag</h3>
        <div class="flag-box">{{ user_flag }}</div>
    </div>
    <div class="card">
        <h3>System Secrets</h3>
        <div class="flag-box">Root Flag: {{ root_flag }}</div>
    </div>
    <p><a href="/">Dashboard</a> | <a href="/logout">Logout</a></p>
</div>
</body>
</html>
"""


@app.route("/admin")
def admin():
    token = request.cookies.get("session_token")
    user = get_user_by_token(token) if token else None

    if not user or user["role"] != "admin":
        return "403 Forbidden - Admin access required.", 403

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

    return render_template_string(ADMIN_HTML, user_flag=user_flag, root_flag=root_flag)


@app.route("/.status/<path:filename>")
def serve_status(filename):
    return send_from_directory("/var/www/html/.status", filename)


@app.route("/logout")
def logout():
    resp = make_response(redirect("/"))
    resp.delete_cookie("session_token")
    return resp


@app.route("/robots.txt")
def robots():
    return "User-agent: *\nDisallow: /admin/\nDisallow: /api/\nDisallow: /.status/\n", 200, {"Content-Type": "text/plain"}


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8080, debug=False)
