#!/usr/bin/env python3
"""
AssetDB - GraphQL Asset Management API
========================================
A deliberately vulnerable Flask + GraphQL application for cybersecurity training.

Vulnerabilities:
  1. GraphQL introspection enabled in production (CWE-200)
  2. SQL injection in searchAssets resolver (CWE-89)
  3. Sensitive data in database accessible via SQLi
"""

import os
import sqlite3
import hashlib

import graphene
from flask import Flask, request, jsonify
from flask_graphql import GraphQLView

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

app = Flask(__name__)
DB_PATH = "/tmp/assetdb.sqlite"


def _read_flag(path):
    try:
        with open(path, "r") as f:
            return f.read().strip()
    except Exception:
        return "FLAG_FILE_NOT_FOUND"


# ---------------------------------------------------------------------------
# Database initialization
# ---------------------------------------------------------------------------


def init_db():
    """Initialize SQLite database with sample data."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            value TEXT NOT NULL,
            location TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT,
            role TEXT DEFAULT 'user'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS secrets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT NOT NULL
        )
    """)

    # Seed assets
    assets = [
        ("Web Server Alpha", "server", "$12,000", "Rack A-1"),
        ("Database Server Beta", "server", "$18,500", "Rack A-2"),
        ("Network Switch Core", "network", "$4,200", "Rack B-1"),
        ("Firewall Appliance", "security", "$8,900", "Rack B-2"),
        ("Load Balancer", "network", "$6,500", "Rack C-1"),
        ("Backup NAS", "storage", "$3,200", "Rack C-2"),
        ("Development Workstation", "workstation", "$2,800", "Office 301"),
        ("Security Camera System", "security", "$1,500", "Building Perimeter"),
    ]

    cursor.execute("SELECT COUNT(*) FROM assets")
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            "INSERT INTO assets (name, category, value, location) VALUES (?, ?, ?, ?)",
            assets
        )

    # Seed users
    user_flag = _read_flag("/home/webapp/user.txt")
    users_data = [
        ("admin", hashlib.sha256("Adm1n!DB#2024".encode()).hexdigest(),
         "admin@assetdb.internal", "admin"),
        ("dbadmin", hashlib.sha256("db-backup-pass!".encode()).hexdigest(),
         "dbadmin@assetdb.internal", "dba"),
        ("auditor", hashlib.sha256("audit2024".encode()).hexdigest(),
         f"sqli_confirmed_{user_flag}", "auditor"),
    ]

    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            "INSERT INTO users (username, password, email, role) VALUES (?, ?, ?, ?)",
            users_data
        )

    # Seed secrets
    root_flag = _read_flag("/root/root.txt")
    introspection_flag = _read_flag("/opt/secrets/introspection_flag.txt")
    secrets_data = [
        ("db_encryption_key", "aes256-k3y-c4f2a9b8e1d7f3a6"),
        ("api_master_token", "assetdb-master-tk-9a8b7c6d5e"),
        ("introspection_token", introspection_flag),
        ("root_flag", root_flag),
        ("backup_password", "bkp!2024$ecure"),
    ]

    cursor.execute("SELECT COUNT(*) FROM secrets")
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            "INSERT INTO secrets (key, value) VALUES (?, ?)",
            secrets_data
        )

    conn.commit()
    conn.close()


def get_db():
    return sqlite3.connect(DB_PATH)


# ---------------------------------------------------------------------------
# GraphQL Schema
# ---------------------------------------------------------------------------


class AssetType(graphene.ObjectType):
    id = graphene.Int()
    name = graphene.String()
    category = graphene.String()
    value = graphene.String()
    location = graphene.String()


class UserType(graphene.ObjectType):
    id = graphene.Int()
    username = graphene.String()
    role = graphene.String()


class Query(graphene.ObjectType):
    status = graphene.String(description="API status and version information")
    assets = graphene.List(AssetType, description="List all assets in the database")
    asset = graphene.Field(AssetType, id=graphene.Int(required=True),
                           description="Get a specific asset by ID")
    search_assets = graphene.List(
        AssetType,
        search=graphene.String(required=True),
        description="Search assets by name (VULNERABLE TO SQL INJECTION)"
    )
    users = graphene.List(UserType, description="List users (limited info)")

    def resolve_status(self, info):
        recon_flag = _read_flag("/var/www/.config/recon_flag.txt")
        return f"AssetDB v1.5.0 - Online | Assets: 8 | Debug: {recon_flag}"

    def resolve_assets(self, info):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, category, value, location FROM assets")
        rows = cursor.fetchall()
        conn.close()
        return [AssetType(id=r[0], name=r[1], category=r[2], value=r[3], location=r[4])
                for r in rows]

    def resolve_asset(self, info, id):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, category, value, location FROM assets WHERE id = ?", (id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return AssetType(id=row[0], name=row[1], category=row[2], value=row[3], location=row[4])
        return None

    def resolve_search_assets(self, info, search):
        """
        VULNERABILITY: SQL Injection
        ============================
        The search parameter is concatenated directly into the SQL query
        without parameterization. This allows UNION-based SQL injection
        to extract data from any table in the database.
        """
        conn = get_db()
        cursor = conn.cursor()

        # BUG: Direct string concatenation - SQL injection!
        query = f"SELECT id, name, category, value, location FROM assets WHERE name LIKE '%{search}%'"

        try:
            cursor.execute(query)
            rows = cursor.fetchall()
        except Exception as e:
            conn.close()
            return [AssetType(id=0, name=f"SQL Error: {str(e)}", category="error",
                            value="", location="")]

        conn.close()
        return [AssetType(id=r[0], name=r[1], category=r[2], value=r[3], location=r[4])
                for r in rows]

    def resolve_users(self, info):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, role FROM users")
        rows = cursor.fetchall()
        conn.close()
        return [UserType(id=r[0], username=r[1], role=r[2]) for r in rows]


schema = graphene.Schema(query=Query)

# ---------------------------------------------------------------------------
# Flask routes
# ---------------------------------------------------------------------------


@app.route("/")
def index():
    return jsonify({
        "application": "AssetDB",
        "version": "1.5.0",
        "api_type": "GraphQL",
        "endpoint": "/graphql",
        "message": "Asset management system. Send GraphQL queries to /graphql.",
    })


# Add GraphQL endpoint with introspection ENABLED (vulnerability)
app.add_url_rule(
    "/graphql",
    view_func=GraphQLView.as_view(
        "graphql",
        schema=schema,
        graphiql=True,  # GraphiQL IDE enabled in production
    )
)


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found", "hint": "The GraphQL endpoint is at /graphql"}), 404


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    init_db()
    print("=" * 60)
    print("  AssetDB v1.5.0 - GraphQL Asset Management API")
    print("  Listening on http://0.0.0.0:4000")
    print("  GraphQL Endpoint: /graphql")
    print("  GraphiQL IDE: /graphql (browser)")
    print("=" * 60)
    app.run(host="0.0.0.0", port=4000, debug=False)
