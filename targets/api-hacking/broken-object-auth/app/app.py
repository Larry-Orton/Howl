#!/usr/bin/env python3
"""
CloudNotes - Cloud Note-Taking API
====================================
A deliberately vulnerable Flask application for cybersecurity training.

Vulnerabilities:
  1. Broken Object-Level Authorization (BOLA/CWE-285)
  2. API checks authentication but not resource ownership
  3. Any authenticated user can access/modify any user's resources
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

JWT_SECRET = "cloudnotes-jwt-2024-secret"
JWT_ALGORITHM = "HS256"

# ---------------------------------------------------------------------------
# In-memory data stores
# ---------------------------------------------------------------------------

users_by_id = {}
users_by_username = {}
user_notes = {}     # { user_id: [ { id, title, content, created_at } ] }
user_settings = {}  # { user_id: { theme, notifications, debug_mode, ... } }
next_user_id = 1
next_note_id = 1


def _hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def _read_flag(path):
    try:
        with open(path, "r") as f:
            return f.read().strip()
    except Exception:
        return "FLAG_FILE_NOT_FOUND"


def _create_user(username, password, role="user", email=None):
    global next_user_id
    user = {
        "id": next_user_id,
        "username": username,
        "password": _hash_password(password),
        "role": role,
        "email": email or f"{username}@cloudnotes.internal",
        "created_at": "2024-01-15T09:00:00Z",
    }
    users_by_id[next_user_id] = user
    users_by_username[username] = user

    # Initialize settings
    user_settings[next_user_id] = {
        "theme": "dark" if role == "admin" else "light",
        "notifications": True,
        "debug_mode": False,
        "timezone": "UTC",
        "language": "en",
    }

    user_notes[next_user_id] = []
    next_user_id += 1
    return user


def _add_note(user_id, title, content):
    global next_note_id
    note = {
        "id": next_note_id,
        "title": title,
        "content": content,
        "created_at": "2024-01-15T09:00:00Z",
        "updated_at": "2024-01-15T09:00:00Z",
    }
    user_notes[user_id].append(note)
    next_note_id += 1
    return note


def _seed_data():
    user_flag = _read_flag("/home/webapp/user.txt")
    auth_flag = _read_flag("/opt/secrets/auth_flag.txt")

    # Admin user (ID 1)
    admin = _create_user("admin", "Cl0ud!N0t3s#Adm1n2024", role="admin",
                         email="admin@cloudnotes.internal")
    _add_note(admin["id"], "System Configuration",
              f"Database: postgresql://admin:Pr0d#2024@db.internal:5432/cloudnotes\n"
              f"Redis: redis://cache.internal:6379\n"
              f"Admin Flag: {user_flag}")
    _add_note(admin["id"], "Security Audit TODO",
              "- Review API authorization checks\n"
              "- Implement object-level access control\n"
              "- Add rate limiting to login endpoint\n"
              "- Rotate JWT signing keys")
    _add_note(admin["id"], "API Keys",
              "Production API Key: cn-prod-k3y-a8f3e2c1d9b7\n"
              "Staging API Key: cn-stg-k3y-1a2b3c4d5e6f\n"
              "DO NOT SHARE THESE WITH ANYONE")

    # Developer user (ID 2)
    dev = _create_user("developer", "dev2024!", role="developer",
                       email="dev@cloudnotes.internal")
    _add_note(dev["id"], "Sprint Notes",
              "Sprint 14: Implement user settings API\n"
              "Note: Skipping authorization checks for now, will add later.\n"
              f"Auth verification token: {auth_flag}")
    _add_note(dev["id"], "Deployment Notes",
              "Deploy v2.3.0 to production\n"
              "Remember to disable debug mode in prod settings")

    # Regular user (ID 3)
    user = _create_user("jsmith", "john2024", role="user",
                        email="jsmith@cloudnotes.internal")
    _add_note(user["id"], "Meeting Notes",
              "Q1 Review meeting at 2pm\n"
              "Discuss budget allocation for security team")


_seed_data()

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
    return _decode_token(auth[7:])


# ---------------------------------------------------------------------------
# Public routes
# ---------------------------------------------------------------------------


@app.route("/")
def index():
    return jsonify({
        "application": "CloudNotes",
        "version": "2.3.0",
        "message": "Cloud note-taking API. See /api/docs for endpoints."
    })


@app.route("/api/docs", methods=["GET"])
def api_docs():
    recon_flag = _read_flag("/var/www/.config/recon_flag.txt")

    endpoints = [
        {"method": "GET", "path": "/", "description": "API info", "auth": False},
        {"method": "GET", "path": "/api/docs", "description": "API documentation", "auth": False},
        {"method": "POST", "path": "/api/register", "description": "Register user", "auth": False,
         "body": {"username": "string", "password": "string"}},
        {"method": "POST", "path": "/api/login", "description": "Authenticate", "auth": False},
        {"method": "GET", "path": "/api/me", "description": "Current user info", "auth": True},
        {"method": "GET", "path": "/api/users/<id>/notes", "description": "Get user's notes", "auth": True},
        {"method": "POST", "path": "/api/users/<id>/notes", "description": "Create a note", "auth": True},
        {"method": "GET", "path": "/api/users/<id>/settings", "description": "Get user settings", "auth": True},
        {"method": "PATCH", "path": "/api/users/<id>/settings", "description": "Update user settings",
         "auth": True, "body": {"key": "value"}},
    ]
    return jsonify({
        "application": "CloudNotes",
        "version": "2.3.0",
        "endpoints": endpoints,
        "total_users": len(users_by_id),
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

    auth_flag = _read_flag("/opt/secrets/auth_flag.txt")

    return jsonify({
        "message": f"User '{username}' registered successfully",
        "user_id": user["id"],
        "token": token,
        "welcome_token": auth_flag,
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
        return jsonify({"error": "Invalid credentials"}), 401

    token = _create_token(user["id"], username, user["role"])
    return jsonify({
        "message": "Login successful",
        "user_id": user["id"],
        "token": token,
    }), 200


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
    }), 200


# ---------------------------------------------------------------------------
# Notes routes - VULNERABLE TO BOLA
# ---------------------------------------------------------------------------


@app.route("/api/users/<int:uid>/notes", methods=["GET"])
def get_notes(uid):
    """
    VULNERABILITY: Broken Object-Level Authorization
    =================================================
    The API checks that the user is authenticated but does NOT check
    that the authenticated user owns the notes being requested.
    Any authenticated user can access any other user's notes.
    """
    payload = _get_current_user()
    if not payload:
        return jsonify({"error": "Authentication required"}), 401

    # BUG: No check that payload["user_id"] == uid
    if uid not in user_notes:
        return jsonify({"error": "User not found"}), 404

    notes = user_notes[uid]
    owner = users_by_id.get(uid, {})

    return jsonify({
        "user_id": uid,
        "owner": owner.get("username", "unknown"),
        "notes": notes,
        "total": len(notes),
    }), 200


@app.route("/api/users/<int:uid>/notes", methods=["POST"])
def create_note(uid):
    """Also vulnerable to BOLA - can create notes in other users' accounts."""
    payload = _get_current_user()
    if not payload:
        return jsonify({"error": "Authentication required"}), 401

    # BUG: No ownership check
    if uid not in user_notes:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json(silent=True)
    if not data or "title" not in data or "content" not in data:
        return jsonify({"error": "JSON body with 'title' and 'content' required"}), 400

    note = _add_note(uid, data["title"], data["content"])
    return jsonify({"message": "Note created", "note": note}), 201


# ---------------------------------------------------------------------------
# Settings routes - VULNERABLE TO BOLA
# ---------------------------------------------------------------------------


@app.route("/api/users/<int:uid>/settings", methods=["GET"])
def get_settings(uid):
    """
    VULNERABILITY: Broken Object-Level Authorization
    Can read any user's settings. When debug_mode is enabled,
    additional sensitive data is included in the response.
    """
    payload = _get_current_user()
    if not payload:
        return jsonify({"error": "Authentication required"}), 401

    # BUG: No ownership check
    if uid not in user_settings:
        return jsonify({"error": "User not found"}), 404

    settings = user_settings[uid].copy()
    owner = users_by_id.get(uid, {})

    response = {
        "user_id": uid,
        "owner": owner.get("username", "unknown"),
        "settings": settings,
    }

    # If debug_mode is enabled, expose sensitive information
    if settings.get("debug_mode"):
        root_flag = _read_flag("/root/root.txt")
        response["debug_info"] = {
            "jwt_secret": JWT_SECRET,
            "database_url": "postgresql://admin:Pr0d#2024@db.internal:5432/cloudnotes",
            "debug_secret": root_flag,
            "internal_api_key": "cn-internal-k3y-x9y8z7w6v5",
        }

    return jsonify(response), 200


@app.route("/api/users/<int:uid>/settings", methods=["PATCH"])
def update_settings(uid):
    """
    VULNERABILITY: Broken Object-Level Authorization
    Can modify any user's settings, including enabling debug_mode
    on the admin account to expose sensitive information.
    """
    payload = _get_current_user()
    if not payload:
        return jsonify({"error": "Authentication required"}), 401

    # BUG: No ownership check
    if uid not in user_settings:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    # Update only provided fields
    allowed_fields = {"theme", "notifications", "debug_mode", "timezone", "language"}
    updated = []
    for key, value in data.items():
        if key in allowed_fields:
            user_settings[uid][key] = value
            updated.append(key)

    return jsonify({
        "message": "Settings updated",
        "updated_fields": updated,
        "settings": user_settings[uid],
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
    print("  CloudNotes v2.3.0 - Cloud Note-Taking API")
    print("  Listening on http://0.0.0.0:3000")
    print("=" * 60)
    app.run(host="0.0.0.0", port=3000, debug=False)
