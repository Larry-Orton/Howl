"""ClockWork Systems - Monitoring Dashboard (leaks credentials via debug endpoint)."""

from flask import Flask

app = Flask(__name__)


@app.route("/")
def index():
    """Main monitoring dashboard."""
    return """<!DOCTYPE html>
<html>
<head><title>ClockWork Systems - Monitoring</title></head>
<body>
<h1>ClockWork Systems</h1>
<h2>Server Monitoring Dashboard</h2>
<table border="1" cellpadding="8">
  <tr><th>Service</th><th>Status</th><th>Uptime</th></tr>
  <tr><td>SSH</td><td style="color:green">ONLINE</td><td>45d 12h</td></tr>
  <tr><td>Cron Service</td><td style="color:green">ONLINE</td><td>45d 12h</td></tr>
  <tr><td>Web Dashboard</td><td style="color:green">ONLINE</td><td>45d 12h</td></tr>
</table>
<br>
<p><a href="/alerts">View Alerts</a></p>
</body>
</html>"""


@app.route("/alerts")
def alerts():
    """Alerts page."""
    return """<!DOCTYPE html>
<html>
<head><title>ClockWork - Alerts</title></head>
<body>
<h1>System Alerts</h1>
<p style="color:orange">[WARN] Disk usage at 72% on /dev/sda1</p>
<p style="color:green">[OK] All cron jobs executing on schedule</p>
<p style="color:green">[OK] SSH service healthy</p>
<p><a href="/">Back</a></p>
</body>
</html>"""


@app.route("/debug")
def debug():
    """Debug endpoint - VULNERABLE: exposes system info and credentials."""
    return """<!DOCTYPE html>
<html>
<head><title>ClockWork - Debug</title></head>
<body>
<h1>Debug Information</h1>
<p style="color:red"><strong>WARNING: This page should not be accessible in production!</strong></p>
<h3>Service Accounts</h3>
<pre>
Monitoring Account:
  Username: monitor
  Password: Cl0ckW0rk_M0n!t0r
  Access: SSH (port 22)

Note: This account is used by the automated monitoring scripts.
Do NOT change the password without updating the cron jobs.
</pre>
<h3>Scheduled Tasks</h3>
<pre>
- /opt/scripts/cleanup.sh (every minute, runs as root)
- /opt/scripts/health_check.sh (every 5 minutes)
</pre>
<!-- Recon flag stored at: /var/www/.config/recon_flag.txt -->
<p><a href="/">Back to Dashboard</a></p>
</body>
</html>"""


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
