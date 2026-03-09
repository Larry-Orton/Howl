"""PathFinder Technologies - Internal Portal (leaks credentials via config page)."""

from flask import Flask

app = Flask(__name__)


@app.route("/")
def index():
    """Main landing page."""
    return """<!DOCTYPE html>
<html>
<head><title>PathFinder Technologies - Portal</title></head>
<body>
<h1>PathFinder Technologies</h1>
<h2>Internal Employee Portal</h2>
<ul>
  <li><a href="/tools">System Tools</a></li>
  <li><a href="/docs">Documentation</a></li>
</ul>
</body>
</html>"""


@app.route("/tools")
def tools():
    """System tools page."""
    return """<!DOCTYPE html>
<html>
<head><title>PathFinder - System Tools</title></head>
<body>
<h1>System Tools</h1>
<p>The following custom tools are available on the server:</p>
<ul>
  <li><strong>/usr/local/bin/sysinfo</strong> - System information utility (SUID enabled for all users)</li>
  <li><strong>/usr/local/bin/backup</strong> - Backup utility (admin only)</li>
</ul>
<p><a href="/">Back</a></p>
</body>
</html>"""


@app.route("/docs")
def docs():
    """Documentation page."""
    return """<!DOCTYPE html>
<html>
<head><title>PathFinder - Docs</title></head>
<body>
<h1>Documentation</h1>
<h3>Server Setup Guide</h3>
<p>All custom binaries are installed in /usr/local/bin/.</p>
<p>The sysinfo tool was compiled from C source and calls standard
   system utilities for gathering diagnostic data.</p>
<p><a href="/config">Server Configuration</a></p>
<p><a href="/">Back</a></p>
</body>
</html>"""


@app.route("/config")
def config():
    """Config page - VULNERABLE: exposes SSH credentials."""
    return """<!DOCTYPE html>
<html>
<head><title>PathFinder - Configuration</title></head>
<body>
<h1>Server Configuration</h1>
<p style="color:red">INTERNAL USE ONLY - Do not expose to external networks</p>
<h3>SSH Access</h3>
<pre>
Service Account:
  Username: pathuser
  Password: P4thF1nd3r_2024
  Port: 22

This account has access to run the sysinfo diagnostic tool.
</pre>
<h3>Custom Tools</h3>
<pre>
/usr/local/bin/sysinfo - SUID root, calls: date, hostname, uptime
  NOTE: 'date' is called without full path for portability
</pre>
<!-- Internal: recon flag at /var/www/.config/recon_flag.txt -->
<p><a href="/">Back</a></p>
</body>
</html>"""


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
