#!/usr/bin/env python3
"""Cacheflow Analytics - Web application backed by Redis."""

from flask import Flask, jsonify
import redis
import os

app = Flask(__name__)
r = redis.Redis(host="127.0.0.1", port=6379, decode_responses=True)

HTML = """<!DOCTYPE html>
<html>
<head><title>Cacheflow Analytics</title></head>
<body>
<h1>Cacheflow Analytics Platform</h1>
<p>Real-time data analytics powered by Redis.</p>
<h2>System Status</h2>
<ul>
<li>Redis Backend: <span style="color:green">Connected</span></li>
<li>Data Pipeline: <span style="color:green">Active</span></li>
<li>API Endpoint: /api/stats</li>
</ul>
<p><small>Backend: Redis on port 6379</small></p>
<!-- Debug mode still active. Check .debug directory for diagnostics. -->
</body>
</html>
"""

@app.route("/")
def index():
    return HTML

@app.route("/api/stats")
def stats():
    try:
        info = r.info()
        return jsonify({
            "redis_version": info.get("redis_version"),
            "connected_clients": info.get("connected_clients"),
            "used_memory_human": info.get("used_memory_human"),
            "total_keys": r.dbsize()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
