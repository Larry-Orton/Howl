"""TarPit Backups - Backup Portal (leaks credentials via log viewer)."""

from flask import Flask

app = Flask(__name__)


@app.route("/")
def index():
    """Main backup portal page."""
    return """<!DOCTYPE html>
<html>
<head><title>TarPit Backups - Portal</title></head>
<body>
<h1>TarPit Backups</h1>
<h2>Managed Backup Service</h2>
<ul>
  <li><a href="/status">Backup Status</a></li>
  <li><a href="/logs">Backup Logs</a></li>
  <li><a href="/schedule">Schedule</a></li>
</ul>
</body>
</html>"""


@app.route("/status")
def status():
    """Backup status page."""
    return """<!DOCTYPE html>
<html>
<head><title>TarPit - Backup Status</title></head>
<body>
<h1>Backup Status</h1>
<table border="1" cellpadding="8">
  <tr><th>Job</th><th>Last Run</th><th>Status</th><th>Size</th></tr>
  <tr><td>User Data Backup</td><td>2024-03-08 12:01</td><td style="color:green">SUCCESS</td><td>2.3 MB</td></tr>
  <tr><td>System Config</td><td>2024-03-08 06:00</td><td style="color:green">SUCCESS</td><td>512 KB</td></tr>
</table>
<p><a href="/">Back</a></p>
</body>
</html>"""


@app.route("/logs")
def logs():
    """Log viewer - VULNERABLE: exposes credentials and backup script details."""
    return """<!DOCTYPE html>
<html>
<head><title>TarPit - Backup Logs</title></head>
<body>
<h1>Backup Job Logs</h1>
<pre>
[2024-03-08 12:01:00] Starting backup job: User Data Backup
[2024-03-08 12:01:00] Script: /opt/backup.sh
[2024-03-08 12:01:00] Command: cd /home/backupuser/data && tar cf /backup/archive.tar *
[2024-03-08 12:01:00] Running as: root (via cron)
[2024-03-08 12:01:01] Archive created: /backup/archive.tar (2.3 MB)
[2024-03-08 12:01:01] Backup completed successfully

[2024-03-08 11:00:00] SSH login: backupuser (password: T4rP1t_Bkup#2024)
[2024-03-08 11:00:05] User backupuser uploaded 2 files to /home/backupuser/data/

NOTE: Backup service account credentials above are for automated uploads.
Do not change without updating the backup client configuration.
</pre>
<!-- Debug: recon artifacts at /var/www/.config/ -->
<p><a href="/">Back</a></p>
</body>
</html>"""


@app.route("/schedule")
def schedule():
    """Backup schedule page."""
    return """<!DOCTYPE html>
<html>
<head><title>TarPit - Schedule</title></head>
<body>
<h1>Backup Schedule</h1>
<table border="1" cellpadding="8">
  <tr><th>Job</th><th>Schedule</th><th>Script</th></tr>
  <tr><td>User Data Backup</td><td>Every minute</td><td>/opt/backup.sh</td></tr>
  <tr><td>System Config</td><td>Daily at 06:00</td><td>/opt/sysbackup.sh</td></tr>
</table>
<p>All backup jobs run as root via cron.</p>
<p><a href="/">Back</a></p>
</body>
</html>"""


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
