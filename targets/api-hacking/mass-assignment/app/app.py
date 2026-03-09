#!/usr/bin/env python3
"""
TeamHub API - Team Management Platform
=======================================
A deliberately vulnerable Flask application for cybersecurity training.

Vulnerabilities:
  1. Mass Assignment - registration endpoint accepts and stores all JSON fields
  2. Privileged fields (is_admin, role) can be set by any user during registration
  3. Admin endpoint exposes sensitive configuration data
"""

import os
import datetime
import hashlib
import uuid

from flask import Flask, request, jsonify
import jwt

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(24).hex()

JWT_SECRET = "teamhub-jwt-key-2024"
JWT_ALGORITHM = "HS256"

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
        "id": str(uuid.uuid4()),
        "username": "admin",
        "password": _hash_password("$uP3r$3cur3!Adm1nPwd#2024"),
        "role": "admin",
        "is_admin": True,
        "email": "admin@teamhub.internal",
        "department": "Engineering",
    }
    users["jdoe"] = {
        "id": str(uuid.uuid4()),
        "username": "jdoe",
        "password": _hash_password("johndoe2024"),
        "role": "user",
        "is_admin": False,
        "email": "jdoe@teamhub.internal",
        "department": "Marketing",
    }


_seed_users()

# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------


def _create_token(username, role, is_admin):
    payload = {
        "username": username,
        "role": role,
        "is_admin": is_admin,
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
# Public routes
# ---------------------------------------------------------------------------


@app.route("/")
def index():
    return jsonify({
        "application": "TeamHub API",
        "version": "1.3.0",
        "message": "Team management platform. See /api/docs for endpoints."
    })


@app.route("/api/docs", methods=["GET"])
def api_docs():
    recon_flag = _read_flag("/var/www/.config/recon_flag.txt")
    endpoints = [
        {"method": "GET", "path": "/", "description": "API info", "auth": False},
        {"method": "GET", "path": "/api/docs", "description": "API documentation", "auth": False},
        {"method": "POST", "path": "/api/register", "description": "Register new user", "auth": False,
         "body": {"username": "string", "password": "string"}},
        {"method": "POST", "path": "/api/login", "description": "Authenticate user", "auth": False},
        {"method": "GET", "path": "/api/profile", "description": "Get current user profile", "auth": True},
        {"method": "GET", "path": "/api/team", "description": "List team members", "auth": True},
        {"method": "GET", "path": "/api/admin/config", "description": "System configuration", "auth": True,
         "note": "Requires admin privileges"},
    ]
    return jsonify({
        "application": "TeamHub API",
        "version": "1.3.0",
        "endpoints": endpoints,
        "internal_note": f"API discovery token: {recon_flag}",
    })


# ---------------------------------------------------------------------------
# Authentication routes
# ---------------------------------------------------------------------------


@app.route("/api/register", methods=["POST"])
def register():
    """
    VULNERABILITY: Mass Assignment
    ==============================
    The registration endpoint takes ALL fields from the JSON body and stores
    them directly in the user record. An attacker can inject is_admin=true
    and role=admin to gain admin privileges.
    """
    data = request.get_json(silent=True)
    if not data or "username" not in data or "password" not in data:
        return jsonify({"error": "JSON body with 'username' and 'password' required"}), 400

    username = data["username"].strip()
    password = data["password"].strip()

    if not username or not password:
        return jsonify({"error": "Username and password must not be empty"}), 400

    if username in users:
        return jsonify({"error": "Username already taken"}), 409

    # BUG: Mass assignment - all fields from request body are accepted
    user = {
        "id": str(uuid.uuid4()),
        "username": username,
        "password": _hash_password(password),
        "role": "user",
        "is_admin": False,
        "email": f"{username}@teamhub.internal",
        "department": "Unassigned",
    }

    # Overwrite defaults with ANY extra fields from the request body
    for key, value in data.items():
        if key != "password":
            user[key] = value

    users[username] = user

    user_flag = _read_flag("/home/webapp/user.txt")

    response = {
        "message": f"User '{username}' registered successfully",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "role": user["role"],
            "is_admin": user["is_admin"],
            "email": user["email"],
            "department": user["department"],
        },
        "token": _create_token(username, user["role"], user["is_admin"]),
    }

    # If user managed to get admin, include the user flag as confirmation
    if user.get("is_admin") is True or user.get("role") == "admin":
        response["admin_welcome"] = f"Welcome to the admin team! Verification: {user_flag}"

    return jsonify(response), 201


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(silent=True)
    if not data or "username" not in data or "password" not in data:
        return jsonify({"error": "JSON body with 'username' and 'password' required"}), 400

    username = data["username"].strip()
    password = data["password"].strip()

    user = users.get(username)
    if not user or user["password"] != _hash_password(password):
        return jsonify({"error": "Invalid username or password"}), 401

    token = _create_token(username, user["role"], user["is_admin"])
    return jsonify({
        "message": "Login successful",
        "token": token,
    }), 200


# ---------------------------------------------------------------------------
# Authenticated routes
# ---------------------------------------------------------------------------


@app.route("/api/profile", methods=["GET"])
def profile():
    payload = _get_current_user()
    if not payload:
        return jsonify({"error": "Authentication required"}), 401

    user = users.get(payload["username"])
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "id": user["id"],
        "username": user["username"],
        "role": user["role"],
        "is_admin": user["is_admin"],
        "email": user["email"],
        "department": user["department"],
    }), 200


@app.route("/api/team", methods=["GET"])
def team():
    payload = _get_current_user()
    if not payload:
        return jsonify({"error": "Authentication required"}), 401

    members = []
    for u in users.values():
        members.append({
            "username": u["username"],
            "role": u["role"],
            "department": u["department"],
        })

    return jsonify({"team_members": members}), 200


# ---------------------------------------------------------------------------
# Admin routes
# ---------------------------------------------------------------------------


@app.route("/api/admin/config", methods=["GET"])
def admin_config():
    payload = _get_current_user()
    if not payload:
        return jsonify({"error": "Authentication required"}), 401

    if not payload.get("is_admin"):
        return jsonify({"error": "Admin access required. Your is_admin claim is not set to true."}), 403

    root_flag = _read_flag("/root/root.txt")

    return jsonify({
        "system_config": {
            "database_url": "postgresql://teamhub:s3cret@db.internal:5432/teamhub",
            "redis_url": "redis://cache.internal:6379/0",
            "jwt_secret": JWT_SECRET,
            "smtp_host": "mail.internal",
            "smtp_password": "mailpass123",
            "secret_data": root_flag,
            "admin_api_key": "thb-admin-key-a8f3e2c1d9b7",
        },
        "message": "Full system configuration exposed to admin users.",
    }), 200


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found", "hint": "Try GET /api/docs"}), 404


@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"error": "Method not allowed"}), 405


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("  TeamHub API v1.3.0 - Team Management Platform")
    print("  Listening on http://0.0.0.0:3000")
    print("=" * 60)
    app.run(host="0.0.0.0", port=3000, debug=False)
