"""DevOps United - Project Management Tool (leaks credentials via notes)."""

from flask import Flask

app = Flask(__name__)


@app.route("/")
def index():
    """Main page for DevOps United project tool."""
    return """<!DOCTYPE html>
<html>
<head><title>DevOps United - Project Hub</title></head>
<body>
<h1>DevOps United</h1>
<h2>Project Management Hub</h2>
<ul>
  <li><a href="/projects">Active Projects</a></li>
  <li><a href="/notes">Team Notes</a></li>
  <li><a href="/status">System Status</a></li>
</ul>
</body>
</html>"""


@app.route("/projects")
def projects():
    """Project listing page."""
    return """<!DOCTYPE html>
<html>
<head><title>DevOps United - Projects</title></head>
<body>
<h1>Active Projects</h1>
<ul>
  <li>Client Migration - Phase 2 (In Progress)</li>
  <li>Infrastructure Audit Q1 (Completed)</li>
  <li>CI/CD Pipeline Overhaul (Planning)</li>
</ul>
<p><a href="/">Back</a></p>
</body>
</html>"""


@app.route("/notes")
def notes():
    """Team notes page - VULNERABLE: exposes SSH credentials."""
    return """<!DOCTYPE html>
<html>
<head><title>DevOps United - Team Notes</title></head>
<body>
<h1>Team Notes</h1>
<h3>Server Access - Updated 2024-03-01</h3>
<pre>
Dev server access for the team:
  SSH User: devuser
  SSH Pass: DevOps_Temp#2024
  Port: 22

NOTE: This is a temporary account for the migration project.
Please change the password after first login.
- Admin
</pre>
<h3>Reminder</h3>
<p>All team members must use the VPN before accessing production systems.</p>
<p><a href="/">Back</a></p>
</body>
</html>"""


@app.route("/status")
def status():
    """System status page."""
    return """<!DOCTYPE html>
<html>
<head><title>DevOps United - Status</title></head>
<body>
<h1>System Status</h1>
<p>SSH Service: <span style="color:green">ONLINE</span></p>
<p>Web Portal: <span style="color:green">ONLINE</span></p>
<p>Database: <span style="color:green">ONLINE</span></p>
<!-- Debug: config flags at /var/www/.config/ -->
<p><a href="/">Back</a></p>
</body>
</html>"""


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
