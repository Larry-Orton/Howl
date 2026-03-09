#!/usr/bin/env python3
"""
PeopleAPI - User Management REST API
=====================================
A deliberately vulnerable Flask application for cybersecurity training.

Vulnerabilities:
  1. Insecure Direct Object Reference (IDOR) on /api/users/<id>
  2. No authorization checks - any authenticated user can access any profile
  3. Admin data including flags exposed through IDOR
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

JWT_SECRET = "peopleapi-secret-key-2024"
JWT_ALGORITHM = "HS256"

# ---------------------------------------------------------------------------
# In-memory user store with sequential IDs
# ---------------------------------------------------------------------------

users_by_id = {}
users_by_username = {}
next_user_id = 1


def _hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def _read_flag(path):
    try:
        with open(path, "r") as f:
            return f.read().strip()
    except Exception:
        return "FLAG_FILE_NOT_FOUND"


def _create_user(username, password, role="user", email=None, phone=None, secret_notes=None):
    global next_user_id
    user = {
        "id": next_user_id,
        "username": username,
        "password": _hash_password(password),
        "role": role,
        "email": email or f"{username}@peopleapi.internal",
        "phone": phone or "555-0100",
        "created_at": "2024-01-15T09:00:00Z",
        "secret_notes": secret_notes or "",
    }
    users_by_id[next_user_id] = user
    users_by_username[username] = user
    next_user_id += 1
    return user


def _seed_users():
    root_flag = _read_flag("/root/root.txt")
    recon_flag = _read_flag("/var/www/.config/recon_flag.txt")
    user_flag = _read_flag("/home/webapp/user.txt")

    _create_user(
        "admin", "Adm1n!$ecur3#Pwd2024", role="admin",
        email="admin@peopleapi.internal", phone="555-0001",
        secret_notes=f"System admin account. Root credentials backup: {root_flag}"
    )
    _create_user(
        "sarah.chen", "sarah2024!", role="user",
        email="sarah.chen@peopleapi.internal", phone="555-0102",
        secret_notes=f"Employee #1042. Performance review pending. Recon token: {recon_flag}"
    )
    _create_user(
        "james.wilson", "wilson-pass", role="user",
        email="james.wilson@peopleapi.internal", phone="555-0103",
        secret_notes=f"Employee #1043. Has access to staging. User flag backup: {user_flag}"
    )


_seed_users()

# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------


def _create_token(user_id, username, role):
    payload = {
        "user_id": user_id,
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
    token = auth[7:]
    return _decode_token(token)


# ---------------------------------------------------------------------------
# Public routes
# ---------------------------------------------------------------------------


@app.route("/")
def index():
    return jsonify({
        "application": "PeopleAPI",
        "version": "2.1.0",
        "message": "User management API. See /api/docs for endpoints."
    })


@app.route("/api/docs", methods=["GET"])
def api_docs():
    recon_flag = _read_flag("/var/www/.config/recon_flag.txt")
    endpoints = [
        {"method": "GET", "path": "/", "description": "API info", "auth": False},
        {"method": "GET", "path": "/api/docs", "description": "API documentation", "auth": False},
        {"method": "POST", "path": "/api/register", "description": "Register new user", "auth": False,
         "body": {"username": "string", "password": "string"}},
        {"method": "POST", "path": "/api/login", "description": "Authenticate user", "auth": False,
         "body": {"username": "string", "password": "string"}},
        {"method": "GET", "path": "/api/users/<id>", "description": "Get user profile by ID", "auth": True},
        {"method": "GET", "path": "/api/users/<id>/notes", "description": "Get user's private notes", "auth": True},
        {"method": "GET", "path": "/api/me", "description": "Get current user profile", "auth": True},
    ]
    return jsonify({
        "application": "PeopleAPI",
        "version": "2.1.0",
        "total_users": len(users_by_id),
        "endpoints": endpoints,
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

    if not username or not password:
        return jsonify({"error": "Username and password must not be empty"}), 400

    if username in users_by_username:
        return jsonify({"error": "Username already taken"}), 409

    user = _create_user(username, password)
    token = _create_token(user["id"], username, "user")

    return jsonify({
        "message": f"User '{username}' registered successfully",
        "user_id": user["id"],
        "token": token,
    }), 201


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(silent=True)
    if not data or "username" not in data or "password" not in data:
        return jsonify({"error": "JSON body with 'username' and 'password' required"}), 400

    username = data["username"].strip()
    password = data["password"].strip()

    user = users_by_username.get(username)
    if not user or user["password"] != _hash_password(password):
        return jsonify({"error": "Invalid username or password"}), 401

    token = _create_token(user["id"], username, user["role"])
    return jsonify({
        "message": "Login successful",
        "user_id": user["id"],
        "token": token,
    }), 200


# ---------------------------------------------------------------------------
# User data routes - VULNERABLE TO IDOR
# ---------------------------------------------------------------------------


@app.route("/api/me", methods=["GET"])
def get_me():
    payload = _get_current_user()
    if not payload:
        return jsonify({"error": "Authentication required"}), 401

    user = users_by_id.get(payload["user_id"])
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "id": user["id"],
        "username": user["username"],
        "role": user["role"],
        "email": user["email"],
        "phone": user["phone"],
        "created_at": user["created_at"],
    }), 200


@app.route("/api/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    """
    VULNERABILITY: IDOR - No authorization check!
    Any authenticated user can access any other user's profile by ID.
    The endpoint only checks that the requester has a valid token,
    not that they should have access to the requested user's data.
    """
    payload = _get_current_user()
    if not payload:
        return jsonify({"error": "Authentication required"}), 401

    # BUG: No check that payload["user_id"] == user_id
    user = users_by_id.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "id": user["id"],
        "username": user["username"],
        "role": user["role"],
        "email": user["email"],
        "phone": user["phone"],
        "created_at": user["created_at"],
    }), 200


@app.route("/api/users/<int:user_id>/notes", methods=["GET"])
def get_user_notes(user_id):
    """
    VULNERABILITY: IDOR - No authorization check on private notes!
    Returns secret_notes field which may contain flags and sensitive data.
    """
    payload = _get_current_user()
    if not payload:
        return jsonify({"error": "Authentication required"}), 401

    # BUG: No check that the requesting user owns these notes
    user = users_by_id.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "id": user["id"],
        "username": user["username"],
        "secret_notes": user["secret_notes"],
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
    print("  PeopleAPI v2.1.0 - User Management API")
    print("  Listening on http://0.0.0.0:3000")
    print("=" * 60)
    app.run(host="0.0.0.0", port=3000, debug=False)
