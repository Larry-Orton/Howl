#!/usr/bin/env python3
"""Internal Admin Panel - runs on 10.8.0.2:9090 (simulated on localhost:9090).

This simulates the internal admin panel that is only accessible via the
VPN network or SSRF. It requires the internal API token for authentication.
"""

from flask import Flask, request, jsonify
import os

app = Flask(__name__)

VALID_TOKEN = "obs-internal-tk-7f8a9b0c1d2e3f4a"

@app.route("/")
def index():
    return jsonify({
        "service": "Obsidian Internal Admin Panel",
        "note": "Authentication required. Provide X-API-Token header.",
        "endpoints": ["/admin/status", "/admin/flag", "/admin/users"]
    })

@app.route("/admin/status")
def status():
    token = request.headers.get("X-API-Token", "")
    if token != VALID_TOKEN:
        return jsonify({"error": "Unauthorized - Invalid API token"}), 401
    return jsonify({
        "internal_network": "healthy",
        "services": ["admin-panel", "vpn-gateway", "monitoring"],
        "users_online": 5
    })

@app.route("/admin/flag")
def flag():
    token = request.headers.get("X-API-Token", "")
    if token != VALID_TOKEN:
        return jsonify({"error": "Unauthorized - Invalid API token"}), 401

    try:
        root_flag = open("/opt/obsidian/admin/root.txt").read().strip()
    except FileNotFoundError:
        root_flag = "FLAG_NOT_FOUND"

    return jsonify({
        "message": "Congratulations! You have reached the internal admin panel.",
        "root_flag": root_flag
    })

@app.route("/admin/users")
def users():
    token = request.headers.get("X-API-Token", "")
    if token != VALID_TOKEN:
        return jsonify({"error": "Unauthorized - Invalid API token"}), 401
    return jsonify({
        "users": [
            {"username": "admin", "role": "superadmin"},
            {"username": "netops", "role": "operator"},
            {"username": "monitor", "role": "readonly"}
        ]
    })


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=9090)
