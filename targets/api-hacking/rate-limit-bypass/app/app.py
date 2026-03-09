#!/usr/bin/env python3
"""
SecureVault - Credential Management API
=========================================
A deliberately vulnerable Flask application for cybersecurity training.

Vulnerabilities:
  1. Rate limiting based on X-Forwarded-For header (CWE-307)
  2. Attacker can spoof client IP to bypass rate limiter
  3. Admin password is a common dictionary word vulnerable to brute-force
"""

import os
import time
import datetime
import hashlib

from flask import Flask, request, jsonify
import jwt

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(24).hex()

JWT_SECRET = "securevault-jwt-2024"
JWT_ALGORITHM = "HS256"

# Rate limiting configuration
RATE_LIMIT_MAX = 5
RATE_LIMIT_WINDOW = 60  # seconds

# In-memory rate limit tracking: { ip: { "count": int, "reset_at": float } }
rate_limits = {}

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
    # Admin with a common password (brute-forceable)
    users["admin"] = {
        "username": "admin",
        "password": _hash_password("letmein"),
        "role": "admin",
        "email": "admin@securevault.internal",
    }
    users["operator"] = {
        "username": "operator",
        "password": _hash_password("operator2024!"),
        "role": "user",
        "email": "operator@securevault.internal",
    }


_seed_users()

# ---------------------------------------------------------------------------
# Rate Limiting - VULNERABLE IMPLEMENTATION
# ---------------------------------------------------------------------------


def _get_client_ip():
    """
    VULNERABILITY: Trusts X-Forwarded-For header for client identification.
    An attacker can spoof this header to get a new rate limit bucket
    for every request, completely bypassing the rate limiter.
    """
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        # Trust the first IP in X-Forwarded-For chain
        return forwarded.split(",")[0].strip()
    return request.remote_addr


def _check_rate_limit():
    """Check if the current client IP has exceeded the rate limit."""
    client_ip = _get_client_ip()
    now = time.time()

    if client_ip in rate_limits:
        entry = rate_limits[client_ip]
        if now > entry["reset_at"]:
            # Window expired, reset counter
            rate_limits[client_ip] = {"count": 1, "reset_at": now + RATE_LIMIT_WINDOW}
            return True, RATE_LIMIT_MAX - 1
        elif entry["count"] >= RATE_LIMIT_MAX:
            remaining_seconds = int(entry["reset_at"] - now)
            return False, remaining_seconds
        else:
            entry["count"] += 1
            return True, RATE_LIMIT_MAX - entry["count"]
    else:
        rate_limits[client_ip] = {"count": 1, "reset_at": now + RATE_LIMIT_WINDOW}
        return True, RATE_LIMIT_MAX - 1


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
# Public routes
# ---------------------------------------------------------------------------


@app.route("/")
def index():
    return jsonify({
        "application": "SecureVault",
        "version": "3.1.0",
        "message": "Credential management API. See /api/docs for endpoints.",
        "security": "Rate limiting enabled - 5 attempts per 60 seconds",
    })


@app.route("/api/docs", methods=["GET"])
def api_docs():
    recon_flag = _read_flag("/var/www/.config/recon_flag.txt")
    user_flag = _read_flag("/home/webapp/user.txt")

    endpoints = [
        {"method": "GET", "path": "/", "description": "API info", "auth": False},
        {"method": "GET", "path": "/api/docs", "description": "API documentation", "auth": False},
        {"method": "POST", "path": "/api/login", "description": "Authenticate user", "auth": False,
         "rate_limited": True, "body": {"username": "string", "password": "string"}},
        {"method": "GET", "path": "/api/profile", "description": "Get user profile", "auth": True},
        {"method": "GET", "path": "/api/admin/vault", "description": "Admin vault access", "auth": True,
         "note": "Requires admin role"},
    ]
    return jsonify({
        "application": "SecureVault",
        "version": "3.1.0",
        "endpoints": endpoints,
        "rate_limiting": {
            "max_attempts": RATE_LIMIT_MAX,
            "window_seconds": RATE_LIMIT_WINDOW,
            "identification": "client IP via proxy headers",
        },
        "debug_token": recon_flag,
        "rate_bypass_confirmation": user_flag,
    })


# ---------------------------------------------------------------------------
# Authentication routes
# ---------------------------------------------------------------------------


@app.route("/api/login", methods=["POST"])
def login():
    """
    Login endpoint with rate limiting.
    VULNERABILITY: Rate limit uses X-Forwarded-For for client identification.
    """
    allowed, remaining = _check_rate_limit()

    if not allowed:
        return jsonify({
            "error": "Rate limit exceeded",
            "message": f"Too many login attempts. Try again in {remaining} seconds.",
            "hint": "The rate limiter identifies you by your IP address.",
        }), 429

    data = request.get_json(silent=True)
    if not data or "username" not in data or "password" not in data:
        return jsonify({"error": "JSON body with 'username' and 'password' required"}), 400

    username = data["username"].strip()
    password = data["password"].strip()

    user = users.get(username)
    if not user or user["password"] != _hash_password(password):
        response = jsonify({
            "error": "Invalid username or password",
            "attempts_remaining": remaining,
        })
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Limit"] = str(RATE_LIMIT_MAX)
        return response, 401

    token = _create_token(username, user["role"])
    return jsonify({
        "message": "Login successful",
        "token": token,
        "role": user["role"],
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
        "username": user["username"],
        "role": user["role"],
        "email": user["email"],
    }), 200


@app.route("/api/admin/vault", methods=["GET"])
def admin_vault():
    payload = _get_current_user()
    if not payload:
        return jsonify({"error": "Authentication required"}), 401

    if payload.get("role") != "admin":
        return jsonify({"error": "Admin access required"}), 403

    root_flag = _read_flag("/root/root.txt")

    return jsonify({
        "vault": "SecureVault Admin Storage",
        "credentials": [
            {"service": "AWS Production", "access_key": "AKIA...", "secret": "wJalr..."},
            {"service": "Database Master", "host": "db.internal", "password": "Pr0d#DB!2024"},
            {"service": "SMTP Relay", "host": "mail.internal", "password": "smtp-r3lay!"},
        ],
        "master_key": root_flag,
        "message": "Full credential vault accessed successfully.",
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
    print("  SecureVault v3.1.0 - Credential Management API")
    print("  Listening on http://0.0.0.0:3000")
    print("  Rate Limiting: 5 attempts / 60 seconds")
    print("=" * 60)
    app.run(host="0.0.0.0", port=3000, debug=False)
