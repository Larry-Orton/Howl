"""CapStone Analytics - Dashboard (leaks credentials via API health endpoint)."""

import json

from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/")
def index():
    """Main analytics dashboard."""
    return """<!DOCTYPE html>
<html>
<head><title>CapStone Analytics - Dashboard</title></head>
<body>
<h1>CapStone Analytics</h1>
<h2>Data Pipeline Dashboard</h2>
<table border="1" cellpadding="8">
  <tr><th>Pipeline</th><th>Status</th><th>Last Run</th></tr>
  <tr><td>ETL-Daily</td><td style="color:green">OK</td><td>2024-03-08 06:00</td></tr>
  <tr><td>ML-Training</td><td style="color:green">OK</td><td>2024-03-08 02:00</td></tr>
  <tr><td>Report-Gen</td><td style="color:orange">DELAYED</td><td>2024-03-07 23:00</td></tr>
</table>
<br>
<p>API Endpoints: <a href="/api/health">/api/health</a> | <a href="/api/status">/api/status</a></p>
</body>
</html>"""


@app.route("/api/status")
def api_status():
    """Public API status endpoint."""
    return jsonify({
        "service": "CapStone Analytics",
        "status": "operational",
        "version": "2.1.0"
    })


@app.route("/api/health")
def api_health():
    """Health check endpoint - VULNERABLE: exposes credentials and system info."""
    return jsonify({
        "status": "healthy",
        "services": {
            "ssh": {"port": 22, "status": "running"},
            "web": {"port": 8080, "status": "running"},
            "python3": {"capabilities": "cap_setuid+ep", "note": "Required for analytics pipeline"}
        },
        "debug": {
            "ssh_account": {
                "username": "analyst",
                "password": "C4pSt0ne_D4ta!",
                "note": "Service account for data pipeline"
            },
            "flag_hint": "Check /var/www/.config/ for recon artifacts"
        }
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
