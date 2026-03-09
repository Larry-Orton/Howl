"""SysCorp Industries - Employee Portal (leaks credentials for initial access)."""

from flask import Flask, request

app = Flask(__name__)

# Hardcoded credentials (intentionally vulnerable)
VALID_USER = "jmartinez"
VALID_PASS = "Syscorp2024!"


@app.route("/")
def index():
    """Employee portal landing page with login form."""
    return """<!DOCTYPE html>
<html>
<head><title>SysCorp Industries - Employee Portal</title></head>
<body>
<h1>SysCorp Industries</h1>
<h2>Employee Portal</h2>
<form method="POST" action="/login">
  <label>Username:</label><br>
  <input type="text" name="username"><br><br>
  <label>Password:</label><br>
  <input type="password" name="password"><br><br>
  <input type="submit" value="Login">
</form>
<!-- TODO: Remove before production deployment -->
<!-- Default credentials: jmartinez / Syscorp2024! -->
<!-- SSH access enabled for remote employees -->
</body>
</html>"""


@app.route("/login", methods=["POST"])
def login():
    """Handle login - validates credentials."""
    username = request.form.get("username", "")
    password = request.form.get("password", "")

    if username == VALID_USER and password == VALID_PASS:
        return f"""<!DOCTYPE html>
<html>
<head><title>SysCorp - Dashboard</title></head>
<body>
<h1>Welcome, {username}!</h1>
<p>Employee dashboard is under construction.</p>
<p>For remote access, please use SSH on port 22.</p>
<p><a href="/">Logout</a></p>
</body>
</html>"""
    else:
        return """<!DOCTYPE html>
<html>
<head><title>SysCorp - Login Failed</title></head>
<body>
<h1>Login Failed</h1>
<p>Invalid credentials. Please try again.</p>
<p><a href="/">Back to Login</a></p>
</body>
</html>""", 401


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
