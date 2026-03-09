#!/usr/bin/env python3
"""Initialize MongoDB with sample data including admin credentials."""

from pymongo import MongoClient
import time

def init():
    # Wait for MongoDB to be ready
    for _ in range(30):
        try:
            client = MongoClient("mongodb://127.0.0.1:27017/", serverSelectionTimeoutMS=2000)
            client.server_info()
            break
        except Exception:
            time.sleep(1)

    # DataPulse main database
    db = client["datapulse"]

    # Users collection
    db.users.drop()
    db.users.insert_many([
        {
            "email": "admin@datapulse.io",
            "username": "admin",
            "password_hash": "$2b$12$LJ3m4xPb5kQxK9Z.vOhZru8V2e5Y3pW1q6N7d8tX0zU9cR4mA2bCe",
            "plaintext_backup": "D4t4Puls3!Adm1n",
            "role": "admin",
            "created": "2024-01-01"
        },
        {
            "email": "analyst@datapulse.io",
            "username": "analyst",
            "password_hash": "$2b$12$xK9Z.vOhZru8V2e5Y3pW1q6N7d8tX0zU9cR4mA2bCeLJ3m4xPb5kQ",
            "plaintext_backup": "An4lyst2024",
            "role": "user",
            "created": "2024-02-15"
        }
    ])

    # Analytics data
    db.analytics.drop()
    db.analytics.insert_many([
        {"event": "page_view", "count": 15432, "date": "2024-03-01"},
        {"event": "signup", "count": 342, "date": "2024-03-01"},
        {"event": "conversion", "count": 89, "date": "2024-03-01"}
    ])

    # Configuration (sensitive)
    db.config.drop()
    db.config.insert_one({
        "app_name": "DataPulse Analytics",
        "version": "2.8.3",
        "mongodb_uri": "mongodb://127.0.0.1:27017/datapulse",
        "secret_key": "dp-secret-key-x7y8z9",
        "api_key": "dp-api-4a5b6c7d8e9f"
    })

    # Internal database
    internal = client["internal"]
    internal.secrets.drop()
    internal.secrets.insert_one({
        "type": "ssh_key_location",
        "path": "/opt/datapulse/.keys/deploy_key",
        "note": "Deploy key for production server"
    })

    print("MongoDB initialized with sample data.")

if __name__ == "__main__":
    init()
