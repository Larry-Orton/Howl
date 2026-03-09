#!/usr/bin/env python3
"""
ConfigAPI - Configuration Management REST API
===============================================
A deliberately vulnerable Flask application for cybersecurity training.

Vulnerabilities:
  1. Incomplete HTTP method security filter (CWE-285)
  2. Only blocks DELETE and POST on admin routes; PATCH/PUT pass through
  3. Admin data accessible via alternative HTTP verbs
"""

import os
import datetime
import hashlib

from flask import Flask, request, jsonify
import jwt

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(24).hex()

JWT_SECRET = "configapi-jwt-secret-2024"
JWT_ALGORITHM = "HS256"

# Security filter deny-list (intentionally incomplete)
BLOCKED_METHODS = {"DELETE", "POST"}

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
        "password": _hash_password("Cfg!Adm1n#2024$ecure"),
        "role": "admin",
        "email": "admin@configapi.internal",
    }
    users["operator"] = {
        "username": "operator",
        "password": _hash_password("operator123"),
        "role": "operator",
        "email": "operator@configapi.internal",
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


# ---------------------------------------------------------------------------
# Security filter middleware
# ---------------------------------------------------------------------------


@app.before_request
def security_filter():
    """
    VULNERABILITY: Incomplete method filtering.
    Only blocks DELETE and POST on /api/admin/ routes.
    PATCH, PUT, and other methods pass through unfiltered.
    """
    if request.path.startswith("/api/admin/"):
        method = request.method.upper()
        if method in BLOCKED_METHODS:
            return jsonify({
                "error": "Forbidden",
                "message": f"Security filter blocked method: {method}",
                "detail": "This HTTP method is not permitted on admin endpoints by security policy.",
                "blocked_methods": list(BLOCKED_METHODS),
            }), 403


# ---------------------------------------------------------------------------
# Public routes
# ---------------------------------------------------------------------------


@app.route("/")
def index():
    return jsonify({
        "application": "ConfigAPI",
        "version": "2.0.1",
        "message": "Configuration management API. See /api/docs for endpoints.",
        "security": "Method-based access control enabled on admin routes.",
    })


@app.route("/api/docs", methods=["GET"])
def api_docs():
    recon_flag = _read_flag("/var/www/.config/recon_flag.txt")

    endpoints = [
        {"method": "GET", "path": "/", "description": "API info", "auth": False},
        {"method": "GET", "path": "/api/docs", "description": "API documentation", "auth": False},
        {"method": "POST", "path": "/api/register", "description": "Register user", "auth": False},
        {"method": "POST", "path": "/api/login", "description": "Authenticate", "auth": False},
        {"method": "GET", "path": "/api/config", "description": "View app config", "auth": True},
        {"method": "GET/POST/DELETE", "path": "/api/admin/config", "description": "Manage system config",
         "auth": True, "note": "POST and DELETE blocked by security filter"},
        {"method": "GET/POST/DELETE", "path": "/api/admin/users", "description": "User management",
         "auth": True, "note": "POST and DELETE blocked by security filter"},
        {"method": "GET/POST/DELETE", "path": "/api/admin/secrets", "description": "System secrets",
         "auth": True, "note": "POST and DELETE blocked by security filter"},
    ]
    return jsonify({
        "application": "ConfigAPI",
        "version": "2.0.1",
        "endpoints": endpoints,
        "security_policy": {
            "admin_routes": "/api/admin/*",
            "blocked_methods": list(BLOCKED_METHODS),
            "enforcement": "before_request filter",
        },
        "debug_token": recon_flag,
    })


# ---------------------------------------------------------------------------
# Authentication routes
# ---------------------------------------------------------------------------


@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json(silent=True)
    if not data or "username" not in data or "password" not in data:
        return jsonify({"error": "JSON body with 'username' and 'password' required"}), 400

    username = data["username"].strip()
    password = data["password"].strip()

    if username in users:
        return jsonify({"error": "Username already taken"}), 409

    users[username] = {
        "username": username,
        "password": _hash_password(password),
        "role": "user",
        "email": f"{username}@configapi.internal",
    }

    token = _create_token(username, "user")
    return jsonify({"message": "Registered successfully", "token": token}), 201


@app.route("/api/login", methods=["POST"])
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


# ---------------------------------------------------------------------------
# Regular authenticated routes
# ---------------------------------------------------------------------------


@app.route("/api/config", methods=["GET"])
def get_config():
    payload = _get_current_user()
    if not payload:
        return jsonify({"error": "Authentication required"}), 401

    return jsonify({
        "app_name": "ConfigAPI",
        "version": "2.0.1",
        "environment": "production",
        "features": {
            "rate_limiting": True,
            "audit_logging": True,
            "method_filtering": True,
        }
    }), 200


# ---------------------------------------------------------------------------
# Admin routes - protected by (incomplete) security filter
# ---------------------------------------------------------------------------


@app.route("/api/admin/config", methods=["GET", "POST", "DELETE", "PUT", "PATCH"])
def admin_config():
    payload = _get_current_user()
    if not payload:
        return jsonify({"error": "Authentication required"}), 401

    user_flag = _read_flag("/home/webapp/user.txt")

    return jsonify({
        "system_config": {
            "database_host": "db.configapi.internal",
            "database_port": 5432,
            "database_name": "configapi_prod",
            "cache_host": "redis.internal",
            "log_level": "DEBUG",
            "max_connections": 100,
        },
        "access_method": request.method,
        "verb_bypass_confirmation": user_flag,
        "note": f"Accessed via {request.method} - security filter only blocks: {list(BLOCKED_METHODS)}",
    }), 200


@app.route("/api/admin/users", methods=["GET", "POST", "DELETE", "PUT", "PATCH"])
def admin_users():
    payload = _get_current_user()
    if not payload:
        return jsonify({"error": "Authentication required"}), 401

    user_list = []
    for u in users.values():
        user_list.append({
            "username": u["username"],
            "role": u["role"],
            "email": u["email"],
        })

    return jsonify({
        "users": user_list,
        "access_method": request.method,
        "total": len(user_list),
    }), 200


@app.route("/api/admin/secrets", methods=["GET", "POST", "DELETE", "PUT", "PATCH"])
def admin_secrets():
    payload = _get_current_user()
    if not payload:
        return jsonify({"error": "Authentication required"}), 401

    root_flag = _read_flag("/root/root.txt")

    return jsonify({
        "secrets": {
            "jwt_signing_key": JWT_SECRET,
            "database_password": "Pr0d#DB!C0nf1g2024",
            "api_master_key": "cfg-master-k3y-a8f3e2c1d9b7",
            "encryption_key": "aes256-c4f2a9b8e1d7f3a6c8e0b2d4f6a8c0e2",
            "master_secret": root_flag,
        },
        "access_method": request.method,
        "note": f"Secrets accessed via {request.method} verb.",
    }), 200


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found", "hint": "Try GET /api/docs"}), 404


@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"error": "Method not allowed", "hint": "Try other HTTP methods like PATCH, PUT"}), 405


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("  ConfigAPI v2.0.1 - Configuration Management API")
    print("  Listening on http://0.0.0.0:3000")
    print("  Security Filter: Blocking DELETE, POST on /api/admin/")
    print("=" * 60)
    app.run(host="0.0.0.0", port=3000, debug=False)
