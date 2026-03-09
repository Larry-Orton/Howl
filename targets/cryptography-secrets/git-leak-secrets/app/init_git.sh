#!/bin/bash
# Initialize a git repository with secrets in old commits
# This script creates a repo where credentials were committed then "removed"

set -e

REPO_DIR="/app/repo"
mkdir -p "$REPO_DIR"
cd "$REPO_DIR"

git init
git config user.email "dev@devforge.local"
git config user.name "DevForge Developer"

# Commit 1: Initial commit WITH hardcoded credentials (the secret)
cat > config.py << 'PYEOF'
# DevForge Configuration
# Database and Admin credentials

DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "devforge"
DB_USER = "devadmin"
DB_PASSWORD = "D3vF0rge_Adm!n2024"

ADMIN_USERNAME = "devadmin"
ADMIN_PASSWORD = "D3vF0rge_Adm!n2024"

SECRET_KEY = "devforge-super-secret-key-2024"
API_TOKEN = "dfg-tok-a1b2c3d4e5f6g7h8"
PYEOF

cat > app.py << 'PYEOF'
# DevForge Project Manager - Main Application
from flask import Flask
app = Flask(__name__)

@app.route("/")
def index():
    return "<h1>DevForge Project Manager</h1>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
PYEOF

cat > README.md << 'MDEOF'
# DevForge Project Manager
Internal project management tool.
MDEOF

git add -A
git commit -m "Initial commit - project setup with config"

# Commit 2: "Remove" credentials (but they stay in history)
cat > config.py << 'PYEOF'
# DevForge Configuration
# Credentials moved to environment variables

import os

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = int(os.environ.get("DB_PORT", 5432))
DB_NAME = os.environ.get("DB_NAME", "devforge")
DB_USER = os.environ.get("DB_USER", "")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")

ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")

SECRET_KEY = os.environ.get("SECRET_KEY", "change-me")
API_TOKEN = os.environ.get("API_TOKEN", "")
PYEOF

git add -A
git commit -m "Security fix: move credentials to environment variables"

# Commit 3: Add more features
cat >> app.py << 'PYEOF'

@app.route("/projects")
def projects():
    return "<h1>Projects List</h1>"

@app.route("/status")
def status():
    return {"status": "ok", "version": "2.1.0"}
PYEOF

git add -A
git commit -m "Add projects endpoint and status check"

echo "Git repository initialized with secret history."
