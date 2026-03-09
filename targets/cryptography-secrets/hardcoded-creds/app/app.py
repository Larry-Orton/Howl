"""Vantage Industries Inventory Tracker - Vulnerable Flask Application.

WARNING: This application is intentionally vulnerable (CWE-798).
         It contains hardcoded database credentials in the source code.
         DO NOT deploy this in any production environment.
"""

import os

import mysql.connector
from flask import Flask, render_template_string, request, session, redirect, send_from_directory

app = Flask(__name__)
app.secret_key = "vantage-internal-key-2024"

# ==================================================================
# VULNERABILITY: Hardcoded database credentials (CWE-798)
# These credentials should be in environment variables or a vault,
# but the developer hardcoded them directly in the source.
# ==================================================================
DB_HOST = "mysql"
DB_PORT = 3306
DB_USER = "inventory_admin"
DB_PASSWORD = "V@ntage_S3cret!2024"
DB_NAME = "inventory"


def get_db():
    """Get a database connection using hardcoded credentials."""
    return mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
    )


# ------------------------------------------------------------------
# Index
# ------------------------------------------------------------------
INDEX_HTML = """
<!DOCTYPE html>
<html>
<head><title>Vantage Industries - Inventory Tracker</title>
<style>
body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
.container { max-width: 800px; margin: auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
h1 { color: #2c3e50; }
a { color: #3498db; }
.login-form { margin-top: 20px; }
input { padding: 8px; margin: 5px; border: 1px solid #ddd; border-radius: 4px; }
button { padding: 8px 20px; background: #3498db; color: white; border: none; border-radius: 4px; cursor: pointer; }
.error { color: red; margin: 10px 0; }
.success { color: green; margin: 10px 0; }
table { width: 100%; border-collapse: collapse; margin-top: 20px; }
th, td { padding: 10px; border: 1px solid #ddd; text-align: left; }
th { background: #3498db; color: white; }
</style>
</head>
<body>
<div class="container">
<h1>Vantage Industries - Inventory Tracker</h1>
<p>Welcome to the internal inventory management system.</p>
{% if session.get('logged_in') %}
    <p>Logged in as: <strong>{{ session.get('username') }}</strong></p>
    <p><a href="/inventory">View Inventory</a> | <a href="/logout">Logout</a></p>
{% else %}
    <h3>Employee Login</h3>
    {% if error %}<p class="error">{{ error }}</p>{% endif %}
    <form class="login-form" method="POST" action="/login">
        <input type="text" name="username" placeholder="Username" required>
        <input type="password" name="password" placeholder="Password" required>
        <button type="submit">Login</button>
    </form>
{% endif %}
</div>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(INDEX_HTML, error=None)


# ------------------------------------------------------------------
# Login
# ------------------------------------------------------------------
@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username", "")
    password = request.form.get("password", "")

    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM users WHERE username=%s AND password=%s",
            (username, password),
        )
        user = cursor.fetchone()
        cursor.close()
        db.close()

        if user:
            session["logged_in"] = True
            session["username"] = user["username"]
            session["role"] = user["role"]

            # Read user flag
            try:
                with open("/home/webapp/user.txt") as f:
                    session["user_flag"] = f.read().strip()
            except Exception:
                session["user_flag"] = "[flag not accessible]"

            return redirect("/inventory")
        else:
            return render_template_string(INDEX_HTML, error="Invalid credentials.")
    except Exception as e:
        return render_template_string(INDEX_HTML, error=f"Connection error: {e}")


# ------------------------------------------------------------------
# Inventory (authenticated)
# ------------------------------------------------------------------
INVENTORY_HTML = """
<!DOCTYPE html>
<html>
<head><title>Inventory</title>
<style>
body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
.container { max-width: 900px; margin: auto; background: white; padding: 30px; border-radius: 8px; }
h1 { color: #2c3e50; }
table { width: 100%; border-collapse: collapse; margin-top: 20px; }
th, td { padding: 10px; border: 1px solid #ddd; text-align: left; }
th { background: #3498db; color: white; }
a { color: #3498db; }
.flag-box { background: #e8f5e9; padding: 15px; border-radius: 4px; margin: 15px 0; font-family: monospace; }
</style>
</head>
<body>
<div class="container">
<h1>Inventory Dashboard</h1>
<p>Welcome, {{ session.get('username') }} ({{ session.get('role') }})</p>
{% if session.get('user_flag') %}
<div class="flag-box">User Flag: {{ session.get('user_flag') }}</div>
{% endif %}
<table>
<tr><th>Item</th><th>SKU</th><th>Quantity</th><th>Location</th></tr>
{% for item in items %}
<tr><td>{{ item.name }}</td><td>{{ item.sku }}</td><td>{{ item.quantity }}</td><td>{{ item.location }}</td></tr>
{% endfor %}
</table>
<p><a href="/logout">Logout</a></p>
</div>
</body>
</html>
"""


@app.route("/inventory")
def inventory():
    if not session.get("logged_in"):
        return redirect("/")

    try:
        db = get_db()
        cursor = db.cursor(named_tuple=True)
        cursor.execute("SELECT name, sku, quantity, location FROM inventory")
        items = cursor.fetchall()
        cursor.close()
        db.close()
    except Exception:
        items = []

    return render_template_string(INVENTORY_HTML, items=items)


# ------------------------------------------------------------------
# Debug endpoint - INTENTIONAL VULNERABILITY
# Exposes the application source code
# ------------------------------------------------------------------
@app.route("/debug/source")
def debug_source():
    """Debug endpoint that exposes the application source code."""
    try:
        with open("/app/app.py", "r") as f:
            source = f.read()
        return f"<pre>{source}</pre>", 200, {"Content-Type": "text/html"}
    except Exception as e:
        return f"Error: {e}", 500


@app.route("/debug/config")
def debug_config():
    """Debug endpoint that exposes database configuration."""
    config_info = f"""
    Database Configuration:
    Host: {DB_HOST}
    Port: {DB_PORT}
    User: {DB_USER}
    Password: {DB_PASSWORD}
    Database: {DB_NAME}
    """
    return f"<pre>{config_info}</pre>", 200, {"Content-Type": "text/html"}


# ------------------------------------------------------------------
# Static files and recon targets
# ------------------------------------------------------------------
@app.route("/.config/<path:filename>")
def serve_config(filename):
    return send_from_directory("/var/www/html/.config", filename)


@app.route("/robots.txt")
def robots():
    return "User-agent: *\nDisallow: /debug/\nDisallow: /.config/\n", 200, {"Content-Type": "text/plain"}


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
