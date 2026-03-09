"""KernelSec Industries - System Portal (vulnerable to command injection)."""

import subprocess

from flask import Flask, request

app = Flask(__name__)


@app.route("/")
def index():
    """Main portal page."""
    return """<!DOCTYPE html>
<html>
<head><title>KernelSec Industries - System Portal</title></head>
<body>
<h1>KernelSec Industries</h1>
<h2>System Management Portal</h2>
<ul>
  <li><a href="/syscheck">System Health Check</a></li>
  <li><a href="/info">System Information</a></li>
</ul>
</body>
</html>"""


@app.route("/syscheck", methods=["GET", "POST"])
def syscheck():
    """System health check - VULNERABLE to command injection."""
    output = ""

    if request.method == "POST":
        host = request.form.get("host", "").strip()
        if host:
            try:
                # VULNERABLE: User input passed directly to shell
                result = subprocess.run(
                    f"ping -c 2 {host}",
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                output = result.stdout + result.stderr
            except subprocess.TimeoutExpired:
                output = "Error: Health check timed out."
            except Exception as e:
                output = f"Error: {str(e)}"
        else:
            output = "Please enter a target host."

    return f"""<!DOCTYPE html>
<html>
<head><title>KernelSec - System Health Check</title></head>
<body>
<h1>System Health Check</h1>
<form method="POST">
  <label>Target host for connectivity check:</label><br>
  <input type="text" name="host" placeholder="e.g., 192.168.1.1" size="40"><br><br>
  <input type="submit" value="Run Check">
</form>
<pre>{output}</pre>
<p><a href="/">Back</a></p>
</body>
</html>"""


@app.route("/info")
def info():
    """System information page."""
    try:
        kernel = subprocess.run(
            ["/usr/local/bin/uname", "-r"],
            capture_output=True, text=True, timeout=5
        ).stdout.strip()
    except Exception:
        kernel = "Unknown"

    return f"""<!DOCTYPE html>
<html>
<head><title>KernelSec - System Info</title></head>
<body>
<h1>System Information</h1>
<table border="1" cellpadding="8">
  <tr><th>Property</th><th>Value</th></tr>
  <tr><td>Kernel Version</td><td>{kernel}</td></tr>
  <tr><td>SSH Service</td><td style="color:green">ONLINE (port 22)</td></tr>
  <tr><td>Web Portal</td><td style="color:green">ONLINE (port 8080)</td></tr>
  <tr><td>Security Patches</td><td style="color:red">OUTDATED</td></tr>
</table>
<p style="color:orange">WARNING: Kernel version may be vulnerable to known exploits.</p>
<p>For SSH access, contact the system administrator or check internal documentation.</p>
<!-- Internal: SSH credentials at /opt/.ssh_credentials -->
<!-- Internal: recon flag at /var/www/.config/recon_flag.txt -->
<p><a href="/">Back</a></p>
</body>
</html>"""


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
