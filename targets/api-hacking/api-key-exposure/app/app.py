#!/usr/bin/env python3
"""
DataDash - Data Analytics Dashboard
=====================================
A deliberately vulnerable Flask application for cybersecurity training.

Vulnerabilities:
  1. API key hardcoded in client-side JavaScript (CWE-798)
  2. Admin API key exposed in frontend source code
  3. Protected admin endpoints accessible with the leaked key
"""

import os
import threading

from flask import Flask, request, jsonify, Response

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# The secret API key - this should NEVER be in client-side code
ADMIN_API_KEY = "datadash-admin-key-a8f3b2c1e9d7f4a6"


def _read_flag(path):
    try:
        with open(path, "r") as f:
            return f.read().strip()
    except Exception:
        return "FLAG_FILE_NOT_FOUND"


# ===================================================================
# FRONTEND SERVER (port 8080)
# ===================================================================

frontend = Flask("frontend")


@frontend.route("/")
def frontend_index():
    recon_flag = _read_flag("/var/www/.config/recon_flag.txt")
    user_flag = _read_flag("/home/webapp/user.txt")

    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>DataDash - Analytics Dashboard</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #1a1a2e; color: #eee; }}
        .header {{ background: #16213e; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        h1 {{ color: #0f3460; margin: 0; }}
        .dashboard {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
        .card {{ background: #16213e; padding: 20px; border-radius: 8px; border: 1px solid #0f3460; }}
        .card h3 {{ color: #e94560; margin-top: 0; }}
        .metric {{ font-size: 2em; color: #0f3460; font-weight: bold; }}
        #data-output {{ background: #0a0a1a; padding: 15px; border-radius: 4px; margin-top: 10px;
                        font-family: monospace; white-space: pre-wrap; max-height: 200px; overflow-y: auto; }}
        button {{ background: #e94560; color: white; border: none; padding: 10px 20px; border-radius: 4px;
                 cursor: pointer; font-size: 1em; }}
        button:hover {{ background: #c73e54; }}
    </style>
</head>
<body>
    <div class="header">
        <h1 style="color: #e94560;">DataDash Analytics</h1>
        <p>Real-time data analytics dashboard v2.4.1</p>
    </div>

    <div class="dashboard">
        <div class="card">
            <h3>Active Users</h3>
            <div class="metric">1,247</div>
        </div>
        <div class="card">
            <h3>API Requests (24h)</h3>
            <div class="metric">54,892</div>
        </div>
        <div class="card">
            <h3>Data Points</h3>
            <button onclick="fetchData()">Load Analytics Data</button>
            <div id="data-output">Click button to load data...</div>
        </div>
        <div class="card">
            <h3>System Status</h3>
            <p style="color: #4ecca3;">All systems operational</p>
            <p>API: <span style="color: #4ecca3;">Connected</span></p>
            <p>Cache: <span style="color: #4ecca3;">Active</span></p>
        </div>
    </div>

    <!-- ============================================================ -->
    <!-- VULNERABILITY: API key hardcoded in client-side JavaScript    -->
    <!-- This key should be kept server-side only                     -->
    <!-- ============================================================ -->
    <script>
        // Application configuration - DO NOT MODIFY
        // Last updated: 2024-01-15 by dev team
        const APP_CONFIG = {{
            api_base_url: "http://localhost:3000",
            api_key: "{ADMIN_API_KEY}",
            version: "2.4.1",
            environment: "production",
            debug_mode: false,
            recon_token: "{recon_flag}",
        }};

        // API key confirmation token: {user_flag}

        async function fetchData() {{
            const output = document.getElementById('data-output');
            output.textContent = 'Loading...';
            try {{
                const response = await fetch(APP_CONFIG.api_base_url + '/api/data', {{
                    headers: {{
                        'X-API-Key': APP_CONFIG.api_key,
                        'Content-Type': 'application/json'
                    }}
                }});
                const data = await response.json();
                output.textContent = JSON.stringify(data, null, 2);
            }} catch (e) {{
                output.textContent = 'Error loading data: ' + e.message;
            }}
        }}
    </script>
</body>
</html>"""
    return Response(html, mimetype="text/html")


# ===================================================================
# BACKEND API SERVER (port 3000)
# ===================================================================

api = Flask("api")


def _check_api_key():
    key = request.headers.get("X-API-Key", "")
    return key == ADMIN_API_KEY


@api.route("/")
def api_index():
    return jsonify({
        "application": "DataDash API",
        "version": "2.4.1",
        "message": "Backend API. Requires X-API-Key header for authenticated endpoints."
    })


@api.route("/api/data", methods=["GET"])
def api_data():
    if not _check_api_key():
        return jsonify({"error": "Invalid or missing API key"}), 401

    return jsonify({
        "analytics": {
            "total_users": 1247,
            "active_sessions": 342,
            "api_calls_24h": 54892,
            "avg_response_ms": 45,
            "error_rate": 0.02,
        },
        "top_endpoints": [
            {"path": "/api/data", "calls": 12500},
            {"path": "/api/users", "calls": 8900},
            {"path": "/api/reports", "calls": 6200},
        ],
    }), 200


@api.route("/api/admin/secrets", methods=["GET"])
def api_admin_secrets():
    """
    Protected admin endpoint - should only be accessible server-side.
    But since the API key is leaked in the frontend, anyone can access this.
    """
    if not _check_api_key():
        return jsonify({"error": "Invalid or missing API key"}), 401

    root_flag = _read_flag("/root/root.txt")

    return jsonify({
        "admin_panel": True,
        "database_credentials": {
            "host": "db.datadash.internal",
            "port": 5432,
            "username": "datadash_admin",
            "password": "Dd!Adm1n#Pr0d2024",
        },
        "encryption_keys": {
            "aes_key": "c4f2a9b8e1d7f3a6c8e0b2d4f6a8c0e2",
            "iv": "a1b2c3d4e5f6a7b8",
        },
        "master_flag": root_flag,
        "internal_api_keys": [
            {"service": "payment-gateway", "key": "pgw-k3y-f8a2b1c9d4e7"},
            {"service": "email-service", "key": "eml-k3y-a2b4c6d8e0f1"},
        ],
    }), 200


@api.route("/api/users", methods=["GET"])
def api_users():
    if not _check_api_key():
        return jsonify({"error": "Invalid or missing API key"}), 401

    return jsonify({
        "users": [
            {"id": 1, "username": "admin", "role": "admin", "email": "admin@datadash.io"},
            {"id": 2, "username": "analyst1", "role": "analyst", "email": "analyst1@datadash.io"},
            {"id": 3, "username": "viewer", "role": "viewer", "email": "viewer@datadash.io"},
        ]
    }), 200


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------


@frontend.errorhandler(404)
def frontend_not_found(e):
    return "<h1>404 - Page Not Found</h1>", 404


@api.errorhandler(404)
def api_not_found(e):
    return jsonify({"error": "Endpoint not found"}), 404


# ---------------------------------------------------------------------------
# Startup - run both servers in threads
# ---------------------------------------------------------------------------

def run_frontend():
    frontend.run(host="0.0.0.0", port=8080, debug=False)


def run_api():
    api.run(host="0.0.0.0", port=3000, debug=False)


if __name__ == "__main__":
    print("=" * 60)
    print("  DataDash v2.4.1 - Analytics Dashboard")
    print("  Frontend: http://0.0.0.0:8080")
    print("  API:      http://0.0.0.0:3000")
    print("=" * 60)

    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()

    run_frontend()
