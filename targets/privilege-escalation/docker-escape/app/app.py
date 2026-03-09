"""DockYard Services - Container Management Dashboard (exposes Docker socket info)."""

import json
import os
import subprocess

from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/")
def index():
    """Main dashboard page."""
    return """<!DOCTYPE html>
<html>
<head><title>DockYard Services - Container Management</title></head>
<body>
<h1>DockYard Services</h1>
<h2>Container Management Dashboard</h2>
<ul>
  <li><a href="/containers">Container Status</a></li>
  <li><a href="/images">Available Images</a></li>
  <li><a href="/api-docs">API Documentation</a></li>
</ul>
</body>
</html>"""


@app.route("/containers")
def containers():
    """Container status page - reveals Docker socket information."""
    docker_sock_exists = os.path.exists("/var/run/docker.sock")
    return f"""<!DOCTYPE html>
<html>
<head><title>DockYard - Container Status</title></head>
<body>
<h1>Container Environment</h1>
<table border="1" cellpadding="8">
  <tr><th>Property</th><th>Value</th></tr>
  <tr><td>Docker Socket Mounted</td><td style="color:{'green' if docker_sock_exists else 'red'}">{'YES - /var/run/docker.sock' if docker_sock_exists else 'NO'}</td></tr>
  <tr><td>Docker API Port</td><td>2375 (TCP)</td></tr>
  <tr><td>Container ID</td><td>{os.popen('hostname').read().strip()}</td></tr>
  <tr><td>Running As</td><td>{os.popen('whoami').read().strip()}</td></tr>
</table>
<h3>Management Notes</h3>
<p>Docker socket is mounted for container management purposes.</p>
<p>Docker API is exposed on port 2375 for remote management.</p>
<p style="color:orange">WARNING: No authentication is configured on the Docker API!</p>
<!-- Internal: recon flag at /var/www/.config/recon_flag.txt -->
<p><a href="/">Back</a></p>
</body>
</html>"""


@app.route("/images")
def images():
    """List available Docker images."""
    try:
        result = subprocess.run(
            ["docker", "images", "--format", "{{.Repository}}:{{.Tag}} ({{.Size}})"],
            capture_output=True, text=True, timeout=5
        )
        image_list = result.stdout.strip() or "No images found"
    except Exception:
        image_list = "Unable to query Docker daemon"

    return f"""<!DOCTYPE html>
<html>
<head><title>DockYard - Images</title></head>
<body>
<h1>Available Docker Images</h1>
<pre>{image_list}</pre>
<p><a href="/">Back</a></p>
</body>
</html>"""


@app.route("/api-docs")
def api_docs():
    """API documentation page."""
    return """<!DOCTYPE html>
<html>
<head><title>DockYard - API Docs</title></head>
<body>
<h1>Docker API Documentation</h1>
<h3>Available Endpoints (Port 2375)</h3>
<pre>
GET  /version          - Docker version info
GET  /info             - System-wide information
GET  /containers/json  - List running containers
POST /containers/create - Create a new container
POST /containers/{id}/start - Start a container
GET  /containers/{id}/logs  - Get container logs
</pre>
<h3>Example Usage</h3>
<pre>
curl http://&lt;target&gt;:2375/version
curl http://&lt;target&gt;:2375/containers/json
</pre>
<p style="color:red">NOTE: API has no authentication. Use with caution.</p>
<p><a href="/">Back</a></p>
</body>
</html>"""


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
