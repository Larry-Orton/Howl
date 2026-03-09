#!/usr/bin/env python3
"""Initialize Redis with sample data including leaked credentials."""

import redis
import time

def init():
    r = redis.Redis(host="127.0.0.1", port=6379, decode_responses=True)

    # Wait for Redis to be ready
    for _ in range(30):
        try:
            r.ping()
            break
        except redis.ConnectionError:
            time.sleep(1)

    # Application data
    r.set("app:name", "Cacheflow Analytics")
    r.set("app:version", "3.2.1")
    r.set("app:environment", "production")

    # Session data
    r.hset("session:abc123", mapping={
        "user": "analyst",
        "role": "viewer",
        "login_time": "2024-01-15T09:30:00Z"
    })

    # Admin credentials stored in Redis (the vulnerability)
    r.set("admin:credentials", "admin:C4ch3Fl0w@dm1n!")
    r.set("admin:api_key", "cf-api-key-9a8b7c6d5e4f3g2h1")

    # Analytics data
    r.lpush("analytics:events", "page_view", "login", "data_export", "report_gen")
    r.set("analytics:daily_users", "1247")
    r.set("analytics:total_queries", "89432")

    print("Redis initialized with sample data.")

if __name__ == "__main__":
    init()
