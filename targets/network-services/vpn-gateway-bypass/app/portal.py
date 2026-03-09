#!/usr/bin/env python3
"""Obsidian Security Corp - VPN Web Management Portal (port 443)."""

from flask import Flask, request, jsonify, send_from_directory
import requests
import os
import ssl

app = Flask(__name__)

# Internal API token (leaked via /api/debug)
INTERNAL_API_TOKEN = "obs-internal-tk-7f8a9b0c1d2e3f4a"

INDEX_HTML = """<!DOCTYPE html>
<html>
<head><title>Obsidian Security - VPN Gateway</title></head>
<body style="font-family: Arial; background: #0a0a0a; color: #e0e0e0; max-width: 900px; margin: 50px auto;">
<h1 style="color: #ff6b35;">Obsidian Security Corp</h1>
<h2>VPN Gateway Management Portal</h2>
<hr style="border-color: #333;">
<h3>Services</h3>
<ul>
<li>OpenVPN Gateway - Port 1194 (UDP)</li>
<li>Management Portal - Port 443 (HTTPS)</li>
</ul>
<h3>Quick Links</h3>
<ul>
<li><a href="/downloads" style="color: #ff6b35;">Download VPN Client Configuration</a></li>
<li><a href="/check" style="color: #ff6b35;">Network Connectivity Checker</a></li>
<li><a href="/api/status" style="color: #ff6b35;">Gateway Status API</a></li>
</ul>
<hr style="border-color: #333;">
<p style="color: #666;">Obsidian Security Corp - Secure Access Infrastructure</p>
<!-- Portal version 2.1.3 - .hidden directory contains diagnostics -->
</body>
</html>
"""

DOWNLOADS_HTML = """<!DOCTYPE html>
<html>
<head><title>VPN Downloads</title></head>
<body style="font-family: Arial; background: #0a0a0a; color: #e0e0e0; max-width: 900px; margin: 50px auto;">
<h1 style="color: #ff6b35;">VPN Client Downloads</h1>
<ul>
<li><a href="/downloads/client.ovpn" style="color: #ff6b35;">client.ovpn</a> - OpenVPN client configuration</li>
</ul>
<p>Import this configuration into your OpenVPN client to connect.</p>
<a href="/" style="color: #ff6b35;">Back to Portal</a>
</body>
</html>
"""

CHECK_HTML = """<!DOCTYPE html>
<html>
<head><title>Connectivity Checker</title></head>
<body style="font-family: Arial; background: #0a0a0a; color: #e0e0e0; max-width: 900px; margin: 50px auto;">
<h1 style="color: #ff6b35;">Network Connectivity Checker</h1>
<form method="GET" action="/check">
<label>URL to check:</label><br>
<input type="text" name="url" style="width: 400px; padding: 8px;" placeholder="http://example.com">
<button type="submit" style="padding: 8px 16px;">Check</button>
</form>
<a href="/" style="color: #ff6b35;">Back to Portal</a>
</body>
</html>
"""

@app.route("/")
def index():
    return INDEX_HTML

@app.route("/downloads")
def downloads():
    return DOWNLOADS_HTML

@app.route("/downloads/<path:filename>")
def download_file(filename):
    return send_from_directory("/var/www/portal/downloads", filename)

@app.route("/api/status")
def api_status():
    return jsonify({
        "gateway": "vpn-gw.obsidian.local",
        "status": "operational",
        "vpn_protocol": "OpenVPN",
        "vpn_port": 1194,
        "connected_clients": 23,
        "internal_network": "10.8.0.0/24",
        "uptime": "34d 7h 22m"
    })

@app.route("/api/debug")
def api_debug():
    """Intentionally exposed debug endpoint leaking sensitive info."""
    try:
        cert_flag = open("/opt/obsidian/certs/cert_flag.txt").read().strip()
    except FileNotFoundError:
        cert_flag = "FLAG_NOT_FOUND"

    return jsonify({
        "debug_mode": True,
        "warning": "Debug endpoint active - disable before production",
        "internal_api_token": INTERNAL_API_TOKEN,
        "internal_services": {
            "admin_panel": "10.8.0.2:9090",
            "api_server": "10.8.0.1:8080",
            "monitoring": "10.8.0.3:3000"
        },
        "vpn_config": {
            "cipher": "AES-128-CBC",
            "auth": "SHA1",
            "cert_verify": "disabled",
            "ca_subject": "CN=obsidian-vpn-ca.internal.corp"
        },
        "cert_verification_flag": cert_flag
    })

@app.route("/check")
def check():
    url = request.args.get("url", "")
    if not url:
        return CHECK_HTML

    # SSRF vulnerability - fetches any URL from server side
    try:
        # Pass along any custom headers (including the API token)
        headers = {}
        api_token = request.headers.get("X-API-Token")
        if api_token:
            headers["X-API-Token"] = api_token

        # Internal network simulation: route 10.8.0.x to localhost services
        fetch_url = url.replace("10.8.0.2:9090", "127.0.0.1:9090")
        fetch_url = fetch_url.replace("10.8.0.1:8080", "127.0.0.1:8080")

        resp = requests.get(fetch_url, headers=headers, timeout=5, verify=False)
        result = f"""<!DOCTYPE html>
<html>
<head><title>Check Result</title></head>
<body style="font-family: Arial; background: #0a0a0a; color: #e0e0e0; max-width: 900px; margin: 50px auto;">
<h1 style="color: #ff6b35;">Connectivity Check Result</h1>
<p>URL: {url}</p>
<p>Status: {resp.status_code}</p>
<h3>Response:</h3>
<pre style="background: #1a1a1a; padding: 15px; overflow: auto; border: 1px solid #333;">{resp.text[:5000]}</pre>
<a href="/check" style="color: #ff6b35;">Check Another</a>
</body>
</html>"""
        return result
    except Exception as e:
        return f"""<!DOCTYPE html>
<html>
<head><title>Check Failed</title></head>
<body style="font-family: Arial; background: #0a0a0a; color: #e0e0e0; max-width: 900px; margin: 50px auto;">
<h1 style="color: #ff6b35;">Connectivity Check Failed</h1>
<p>URL: {url}</p>
<p>Error: {str(e)}</p>
<a href="/check" style="color: #ff6b35;">Try Again</a>
</body>
</html>"""


if __name__ == "__main__":
    # Generate self-signed cert for HTTPS
    import subprocess
    if not os.path.exists("/tmp/portal.crt"):
        subprocess.run([
            "openssl", "req", "-x509", "-newkey", "rsa:2048",
            "-keyout", "/tmp/portal.key", "-out", "/tmp/portal.crt",
            "-days", "365", "-nodes",
            "-subj", "/CN=vpn-portal.obsidian.local"
        ], capture_output=True)

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain("/tmp/portal.crt", "/tmp/portal.key")
    app.run(host="0.0.0.0", port=443, ssl_context=context)
