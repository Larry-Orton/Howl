"""CipherStack User Portal - Vulnerable Flask Application.

WARNING: This application is intentionally vulnerable (CWE-328).
         It uses unsalted MD5 for password hashing.
         DO NOT deploy this in any production environment.
"""

import hashlib
import os

import mysql.connector
from flask import Flask, request, session, redirect, jsonify, render_template_string, send_from_directory

app = Flask(__name__)
app.secret_key = "cipherstack-secret-2024"

DB_CONFIG = {
    "host": "mysql",
    "port": 3306,
    "user": "cs_app",
    "password": "cs_db_p@ss2024",
    "database": "cipherstack",
}


def get_db():
    return mysql.connector.connect(**DB_CONFIG)


def md5_hash(password):
    """VULNERABLE: Unsalted MD5 hash (CWE-328)."""
    return hashlib.md5(password.encode()).hexdigest()


# ------------------------------------------------------------------
# Main Page
# ------------------------------------------------------------------
INDEX_HTML = """
<!DOCTYPE html>
<html>
<head><title>CipherStack - User Portal</title>
<style>
body { font-family: 'Segoe UI', sans-serif; margin: 0; background: #1e1e2e; color: #cdd6f4; }
.navbar { background: #181825; padding: 15px 30px; border-bottom: 1px solid #313244; }
.navbar h2 { margin: 0; color: #89b4fa; }
.container { max-width: 800px; margin: 40px auto; padding: 20px; }
.card { background: #181825; padding: 25px; border-radius: 8px; border: 1px solid #313244; margin: 15px 0; }
a { color: #89b4fa; }
input { padding: 10px; margin: 5px; background: #1e1e2e; border: 1px solid #313244; color: #cdd6f4; border-radius: 4px; }
button { padding: 10px 20px; background: #89b4fa; color: #1e1e2e; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; }
.error { color: #f38ba8; }
.success { color: #a6e3a1; }
.flag-box { background: #1e3a1e; padding: 15px; border-radius: 4px; border: 1px solid #a6e3a1; font-family: monospace; margin: 10px 0; }
</style>
</head>
<body>
<div class="navbar">
    <h2>CipherStack</h2>
</div>
<div class="container">
    {% if session.get('logged_in') %}
    <div class="card">
        <h2>Welcome, {{ session.get('username') }}</h2>
        <p>Role: {{ session.get('role') }}</p>
        {% if session.get('user_flag') %}
        <div class="flag-box">User Flag: {{ session.get('user_flag') }}</div>
        {% endif %}
        {% if session.get('role') == 'admin' %}
        <div class="flag-box">Root Flag: {{ session.get('root_flag', '[not accessible]') }}</div>
        {% endif %}
        <p><a href="/users">User Management</a> | <a href="/logout">Logout</a></p>
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
        {% if reg_success %}<p class="success">{{ reg_success }}</p>{% endif %}
        <form method="POST" action="/register">
            <input type="text" name="username" placeholder="Username" required>
            <input type="email" name="email" placeholder="Email" required>
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
    return render_template_string(INDEX_HTML, error=None, reg_success=None)


@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username", "")
    password = request.form.get("password", "")
    password_hash = md5_hash(password)

    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM users WHERE username=%s AND password_hash=%s",
            (username, password_hash),
        )
        user = cursor.fetchone()
        cursor.close()
        db.close()

        if user:
            session["logged_in"] = True
            session["username"] = user["username"]
            session["role"] = user["role"]

            try:
                with open("/home/webapp/user.txt") as f:
                    session["user_flag"] = f.read().strip()
            except Exception:
                session["user_flag"] = "[not accessible]"

            if user["role"] == "admin":
                try:
                    with open("/root/root.txt") as f:
                        session["root_flag"] = f.read().strip()
                except Exception:
                    session["root_flag"] = "[requires root - check /root/root.txt]"

            return redirect("/")
        else:
            return render_template_string(INDEX_HTML, error="Invalid credentials.", reg_success=None)
    except Exception as e:
        return render_template_string(INDEX_HTML, error=f"Error: {e}", reg_success=None)


@app.route("/register", methods=["POST"])
def register():
    username = request.form.get("username", "")
    email = request.form.get("email", "")
    password = request.form.get("password", "")
    password_hash = md5_hash(password)

    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO users (username, email, password_hash, role) VALUES (%s, %s, %s, %s)",
            (username, email, password_hash, "user"),
        )
        db.commit()
        cursor.close()
        db.close()
        return render_template_string(INDEX_HTML, error=None, reg_success="Account created! You can now log in.")
    except Exception as e:
        return render_template_string(INDEX_HTML, error=None, reg_success=f"Registration failed: {e}")


# ------------------------------------------------------------------
# VULNERABILITY: Debug API endpoint exposing user hashes (CWE-538)
# ------------------------------------------------------------------
@app.route("/api/users/debug")
def api_users_debug():
    """Debug endpoint that exposes user data including MD5 password hashes."""
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT id, username, email, password_hash, role FROM users")
        users = cursor.fetchall()
        cursor.close()
        db.close()
        return jsonify({"users": users, "hash_algorithm": "md5", "salt": "none"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/users")
def user_list():
    if not session.get("logged_in"):
        return redirect("/")

    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT id, username, email, role FROM users")
        users = cursor.fetchall()
        cursor.close()
        db.close()
    except Exception:
        users = []

    user_rows = ""
    for u in users:
        user_rows += f"<tr><td>{u['id']}</td><td>{u['username']}</td><td>{u['email']}</td><td>{u['role']}</td></tr>"

    return render_template_string(f"""
    <!DOCTYPE html><html><head><title>Users</title>
    <style>body{{font-family:sans-serif;margin:40px;background:#1e1e2e;color:#cdd6f4;}}
    table{{border-collapse:collapse;width:100%;}} th,td{{padding:10px;border:1px solid #313244;}}
    th{{background:#89b4fa;color:#1e1e2e;}} a{{color:#89b4fa;}}</style>
    </head><body><h2>User Management</h2>
    <table><tr><th>ID</th><th>Username</th><th>Email</th><th>Role</th></tr>
    {user_rows}</table>
    <p><a href="/">Back</a></p></body></html>
    """)


@app.route("/.internal/<path:filename>")
def serve_internal(filename):
    return send_from_directory("/var/www/html/.internal", filename)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/robots.txt")
def robots():
    return "User-agent: *\nDisallow: /api/\nDisallow: /.internal/\n", 200, {"Content-Type": "text/plain"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
