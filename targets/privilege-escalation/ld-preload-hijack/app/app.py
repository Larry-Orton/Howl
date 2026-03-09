"""PreLoad Dynamics - Network Diagnostic Tool (vulnerable to command injection)."""

import subprocess

from flask import Flask, request

app = Flask(__name__)


@app.route("/")
def index():
    """Main page with network diagnostic tool."""
    return """<!DOCTYPE html>
<html>
<head><title>PreLoad Dynamics - Network Diagnostics</title></head>
<body>
<h1>PreLoad Dynamics</h1>
<h2>Network Diagnostic Tool</h2>
<form method="POST" action="/diagnose">
  <label>Enter host to check connectivity:</label><br>
  <input type="text" name="host" placeholder="e.g., 8.8.8.8" size="40"><br><br>
  <input type="submit" value="Run Diagnostic">
</form>
<br>
<p><a href="/about">About this tool</a></p>
</body>
</html>"""


@app.route("/diagnose", methods=["POST"])
def diagnose():
    """Diagnostic endpoint - VULNERABLE to OS command injection."""
    host = request.form.get("host", "").strip()
    output = ""

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
            output = "Error: Diagnostic timed out."
        except Exception as e:
            output = f"Error: {str(e)}"
    else:
        output = "Please enter a host address."

    return f"""<!DOCTYPE html>
<html>
<head><title>PreLoad Dynamics - Results</title></head>
<body>
<h1>Diagnostic Results</h1>
<pre>{output}</pre>
<p><a href="/">Run Another Test</a></p>
</body>
</html>"""


@app.route("/about")
def about():
    """About page."""
    return """<!DOCTYPE html>
<html>
<head><title>PreLoad Dynamics - About</title></head>
<body>
<h1>About</h1>
<p>PreLoad Dynamics Network Diagnostic Tool v1.2</p>
<p>This tool provides basic network connectivity checks for internal hosts.</p>
<p>For SSH access to the server, contact the system administrator.</p>
<!-- Credential backup stored at /opt/.credentials -->
<p><a href="/">Back</a></p>
</body>
</html>"""


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
