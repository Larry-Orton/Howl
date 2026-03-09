#!/usr/bin/env python3
"""
CorpAuth & CorpApp - OAuth 2.0 System
=======================================
A deliberately vulnerable OAuth implementation for cybersecurity training.

Vulnerabilities:
  1. Weak redirect_uri validation - prefix check only (CWE-601)
  2. Open redirect in client application
  3. Authorization code can be stolen via redirect manipulation
  4. No PKCE or state parameter enforcement
"""

import os
import datetime
import hashlib
import uuid
import threading
import urllib.parse

from flask import Flask, request, jsonify, redirect, Response, make_response
import jwt

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

JWT_SECRET = "corpauth-jwt-signing-key-2024"
JWT_ALGORITHM = "HS256"

# Registered OAuth clients
REGISTERED_CLIENTS = {
    "corpapp": {
        "client_id": "corpapp",
        "client_secret": "corpapp-secret",
        "redirect_uri_prefix": "http://localhost:8080/callback",
        "name": "CorpApp - Corporate Application",
    }
}

# OAuth user database
oauth_users = {}
# Authorization codes store: { code: { user, client_id, redirect_uri, expires } }
auth_codes = {}
# Access tokens store: { token: { user, client_id, scope, expires } }
access_tokens = {}


def _hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def _read_flag(path):
    try:
        with open(path, "r") as f:
            return f.read().strip()
    except Exception:
        return "FLAG_FILE_NOT_FOUND"


def _seed_users():
    oauth_users["admin"] = {
        "username": "admin",
        "password": _hash_password("OAuthAdmin2024!"),
        "role": "admin",
        "email": "admin@corp.internal",
        "full_name": "System Administrator",
    }
    oauth_users["employee"] = {
        "username": "employee",
        "password": _hash_password("emp2024"),
        "role": "user",
        "email": "employee@corp.internal",
        "full_name": "John Employee",
    }


_seed_users()


# ===================================================================
# OAUTH AUTHORIZATION SERVER (port 8443)
# ===================================================================

oauth_server = Flask("oauth_server")


@oauth_server.route("/")
def oauth_index():
    return jsonify({
        "service": "CorpAuth OAuth 2.0 Server",
        "version": "1.0.0",
        "endpoints": {
            "authorize": "/oauth/authorize",
            "token": "/oauth/token",
            "userinfo": "/oauth/userinfo",
            "docs": "/oauth/docs",
        }
    })


@oauth_server.route("/oauth/docs", methods=["GET"])
def oauth_docs():
    recon_flag = _read_flag("/var/www/.config/recon_flag.txt")
    redirect_flag = _read_flag("/opt/secrets/redirect_flag.txt")

    return jsonify({
        "service": "CorpAuth OAuth 2.0 Server",
        "version": "1.0.0",
        "grant_types": ["authorization_code"],
        "endpoints": [
            {"method": "GET", "path": "/oauth/authorize",
             "description": "Authorization endpoint - initiates auth code flow",
             "params": ["response_type=code", "client_id", "redirect_uri", "state (optional)"]},
            {"method": "POST", "path": "/oauth/authorize",
             "description": "Submit login credentials during authorization",
             "body": {"username": "string", "password": "string"}},
            {"method": "POST", "path": "/oauth/token",
             "description": "Token endpoint - exchange code for access token",
             "body": {"grant_type": "authorization_code", "code": "string",
                      "client_id": "string", "client_secret": "string", "redirect_uri": "string"}},
            {"method": "GET", "path": "/oauth/userinfo",
             "description": "Get user info with access token", "auth": "Bearer token"},
            {"method": "GET", "path": "/oauth/admin/flag",
             "description": "Admin-only endpoint", "auth": "Bearer token (admin)"},
        ],
        "registered_clients": [
            {"client_id": "corpapp", "name": "CorpApp", "redirect_uri_prefix": "http://localhost:8080/callback"}
        ],
        "debug_info": {
            "recon_token": recon_flag,
            "validation_note": "redirect_uri is validated against registered prefix",
            "redirect_validation_token": redirect_flag,
        },
    })


@oauth_server.route("/oauth/authorize", methods=["GET"])
def authorize_get():
    """Show login form for authorization."""
    response_type = request.args.get("response_type", "")
    client_id = request.args.get("client_id", "")
    redirect_uri = request.args.get("redirect_uri", "")
    state = request.args.get("state", "")

    if response_type != "code":
        return jsonify({"error": "unsupported_response_type",
                       "message": "Only 'code' response type is supported"}), 400

    client = REGISTERED_CLIENTS.get(client_id)
    if not client:
        return jsonify({"error": "invalid_client",
                       "message": f"Unknown client_id: {client_id}"}), 400

    # VULNERABILITY: Weak redirect_uri validation - prefix check only!
    if not redirect_uri.startswith(client["redirect_uri_prefix"]):
        return jsonify({
            "error": "invalid_redirect_uri",
            "message": "redirect_uri does not match registered prefix",
            "expected_prefix": client["redirect_uri_prefix"],
            "received": redirect_uri,
        }), 400

    html = f"""<!DOCTYPE html>
<html>
<head><title>CorpAuth - Login</title>
<style>
    body {{ font-family: Arial, sans-serif; background: #1a1a2e; color: #eee;
           display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
    .login-box {{ background: #16213e; padding: 40px; border-radius: 10px;
                  width: 350px; box-shadow: 0 4px 20px rgba(0,0,0,0.3); }}
    h2 {{ color: #e94560; text-align: center; }}
    input {{ width: 100%; padding: 12px; margin: 8px 0; box-sizing: border-box;
            background: #0f3460; border: 1px solid #533483; color: #eee; border-radius: 4px; }}
    button {{ width: 100%; padding: 12px; background: #e94560; color: white; border: none;
             border-radius: 4px; cursor: pointer; font-size: 1em; margin-top: 10px; }}
    button:hover {{ background: #c73e54; }}
    .info {{ font-size: 0.8em; color: #888; text-align: center; margin-top: 15px; }}
</style>
</head>
<body>
<div class="login-box">
    <h2>CorpAuth Login</h2>
    <p style="text-align:center; color:#888;">Authorize {client['name']}</p>
    <form method="POST">
        <input type="hidden" name="response_type" value="{response_type}" />
        <input type="hidden" name="client_id" value="{client_id}" />
        <input type="hidden" name="redirect_uri" value="{redirect_uri}" />
        <input type="hidden" name="state" value="{state}" />
        <input type="text" name="username" placeholder="Username" required />
        <input type="password" name="password" placeholder="Password" required />
        <button type="submit">Authorize & Login</button>
    </form>
    <p class="info">By logging in, you authorize this application to access your account.</p>
</div>
</body>
</html>"""
    return Response(html, mimetype="text/html")


@oauth_server.route("/oauth/authorize", methods=["POST"])
def authorize_post():
    """Process login and issue authorization code."""
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()
    client_id = request.form.get("client_id", "")
    redirect_uri = request.form.get("redirect_uri", "")
    state = request.form.get("state", "")

    # Authenticate user
    user = oauth_users.get(username)
    if not user or user["password"] != _hash_password(password):
        return jsonify({"error": "access_denied", "message": "Invalid credentials"}), 401

    client = REGISTERED_CLIENTS.get(client_id)
    if not client:
        return jsonify({"error": "invalid_client"}), 400

    # VULNERABILITY: Same weak prefix check
    if not redirect_uri.startswith(client["redirect_uri_prefix"]):
        return jsonify({"error": "invalid_redirect_uri"}), 400

    # Generate authorization code
    code = uuid.uuid4().hex
    auth_codes[code] = {
        "username": username,
        "role": user["role"],
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "expires": datetime.datetime.utcnow() + datetime.timedelta(minutes=10),
    }

    user_flag = _read_flag("/home/webapp/user.txt")
    auth_codes[code]["steal_confirmation"] = user_flag

    # Redirect with code
    separator = "&" if "?" in redirect_uri else "?"
    redirect_url = f"{redirect_uri}{separator}code={code}"
    if state:
        redirect_url += f"&state={state}"

    return redirect(redirect_url)


@oauth_server.route("/oauth/token", methods=["POST"])
def token_endpoint():
    """Exchange authorization code for access token."""
    grant_type = request.form.get("grant_type", "")
    code = request.form.get("code", "")
    client_id = request.form.get("client_id", "")
    client_secret = request.form.get("client_secret", "")
    redirect_uri = request.form.get("redirect_uri", "")

    if grant_type != "authorization_code":
        return jsonify({"error": "unsupported_grant_type"}), 400

    # Verify client credentials
    client = REGISTERED_CLIENTS.get(client_id)
    if not client or client["client_secret"] != client_secret:
        return jsonify({"error": "invalid_client", "message": "Bad client credentials"}), 401

    # Verify authorization code
    code_data = auth_codes.get(code)
    if not code_data:
        return jsonify({"error": "invalid_grant", "message": "Invalid or expired code"}), 400

    if code_data["client_id"] != client_id:
        return jsonify({"error": "invalid_grant", "message": "Code was issued to different client"}), 400

    if datetime.datetime.utcnow() > code_data["expires"]:
        del auth_codes[code]
        return jsonify({"error": "invalid_grant", "message": "Code expired"}), 400

    # Note: In a secure implementation, redirect_uri should be validated here too
    # But we intentionally don't enforce strict matching

    # Generate access token
    access_token = jwt.encode({
        "username": code_data["username"],
        "role": code_data["role"],
        "client_id": client_id,
        "scope": "openid profile",
        "iat": datetime.datetime.utcnow(),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1),
    }, JWT_SECRET, algorithm=JWT_ALGORITHM)

    # Remove used code
    del auth_codes[code]

    return jsonify({
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": 3600,
        "scope": "openid profile",
    }), 200


@oauth_server.route("/oauth/userinfo", methods=["GET"])
def userinfo():
    """Return user info for valid access token."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return jsonify({"error": "invalid_token"}), 401

    try:
        payload = jwt.decode(auth[7:], JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return jsonify({"error": "invalid_token"}), 401

    user = oauth_users.get(payload["username"])
    if not user:
        return jsonify({"error": "user_not_found"}), 404

    return jsonify({
        "sub": payload["username"],
        "name": user["full_name"],
        "email": user["email"],
        "role": user["role"],
    }), 200


@oauth_server.route("/oauth/admin/flag", methods=["GET"])
def admin_flag():
    """Admin-only endpoint returning the root flag."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return jsonify({"error": "invalid_token"}), 401

    try:
        payload = jwt.decode(auth[7:], JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return jsonify({"error": "invalid_token"}), 401

    if payload.get("role") != "admin":
        return jsonify({"error": "forbidden", "message": "Admin access required"}), 403

    root_flag = _read_flag("/root/root.txt")

    return jsonify({
        "message": "Admin access granted",
        "admin_user": payload["username"],
        "root_flag": root_flag,
        "system_secrets": {
            "jwt_key": JWT_SECRET,
            "database": "postgresql://admin:Pr0d#OAuth2024@db.internal:5432/corpauth",
            "ldap_bind": "cn=admin,dc=corp,dc=internal / LdapBind!2024",
        }
    }), 200


@oauth_server.errorhandler(404)
def oauth_not_found(e):
    return jsonify({"error": "not_found", "hint": "See /oauth/docs"}), 404


# ===================================================================
# CLIENT APPLICATION (port 8080)
# ===================================================================

client_app = Flask("client_app")


@client_app.route("/")
def client_index():
    html = """<!DOCTYPE html>
<html>
<head><title>CorpApp - Corporate Application</title>
<style>
    body { font-family: Arial, sans-serif; background: #0a0a1a; color: #eee; padding: 40px; }
    h1 { color: #4ecca3; }
    .btn { display: inline-block; background: #4ecca3; color: #000; padding: 15px 30px;
           text-decoration: none; border-radius: 5px; font-size: 1.1em; margin-top: 20px; }
    .btn:hover { background: #3ba888; }
    .info { background: #16213e; padding: 20px; border-radius: 8px; margin-top: 20px; }
    code { background: #0f3460; padding: 2px 6px; border-radius: 3px; }
</style>
</head>
<body>
    <h1>CorpApp - Corporate Application</h1>
    <p>Welcome to the corporate application. Please log in using your corporate OAuth account.</p>

    <a class="btn" href="http://localhost:8443/oauth/authorize?response_type=code&client_id=corpapp&redirect_uri=http://localhost:8080/callback&state=random123">
        Login with CorpAuth
    </a>

    <div class="info">
        <h3>About</h3>
        <p>OAuth Provider: <code>http://localhost:8443</code></p>
        <p>Client ID: <code>corpapp</code></p>
        <p>Callback URL: <code>http://localhost:8080/callback</code></p>
        <p>Admin contact: admin@corp.internal</p>
        <p><small>Hint: Default admin credentials follow the pattern: OAuthAdmin[year]!</small></p>
    </div>
</body>
</html>"""
    return Response(html, mimetype="text/html")


@client_app.route("/callback")
def callback():
    """OAuth callback handler - exchanges code for token."""
    code = request.args.get("code", "")
    state = request.args.get("state", "")
    error = request.args.get("error", "")

    if error:
        return jsonify({"error": error}), 400

    if not code:
        return jsonify({"error": "No authorization code received"}), 400

    html = f"""<!DOCTYPE html>
<html>
<head><title>CorpApp - Login Success</title>
<style>
    body {{ font-family: Arial, sans-serif; background: #0a0a1a; color: #eee; padding: 40px; }}
    h1 {{ color: #4ecca3; }}
    .code-box {{ background: #16213e; padding: 20px; border-radius: 8px; margin: 20px 0;
                 font-family: monospace; word-break: break-all; }}
    .info {{ color: #888; margin-top: 20px; }}
</style>
</head>
<body>
    <h1>Authorization Successful</h1>
    <p>Authorization code received from CorpAuth:</p>
    <div class="code-box">
        <strong>Code:</strong> {code}<br>
        <strong>State:</strong> {state}
    </div>
    <p>In a production app, this code would be automatically exchanged for an access token.</p>
    <p class="info">To exchange: POST to http://localhost:8443/oauth/token with grant_type=authorization_code, code, client_id, client_secret, redirect_uri</p>
</body>
</html>"""
    return Response(html, mimetype="text/html")


@client_app.route("/redirect")
def open_redirect():
    """
    VULNERABILITY: Open redirect in client application.
    Can be chained with OAuth redirect_uri manipulation to steal auth codes.
    """
    url = request.args.get("url", "/")
    return redirect(url)


@client_app.route("/api/steal")
def steal_endpoint():
    """
    Attacker simulation endpoint - captures stolen authorization codes.
    In a real attack, this would be on the attacker's server.
    """
    code = request.args.get("code", "")
    state = request.args.get("state", "")
    user_flag = _read_flag("/home/webapp/user.txt")

    return jsonify({
        "status": "CODE CAPTURED!",
        "stolen_code": code,
        "state": state,
        "message": "Authorization code successfully intercepted via redirect manipulation",
        "code_theft_confirmation": user_flag,
        "next_step": f"Exchange the code at POST http://localhost:8443/oauth/token with client_id=corpapp, client_secret=corpapp-secret",
    }), 200


@client_app.errorhandler(404)
def client_not_found(e):
    return jsonify({"error": "Page not found"}), 404


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

def run_oauth_server():
    oauth_server.run(host="0.0.0.0", port=8443, debug=False)


def run_client_app():
    client_app.run(host="0.0.0.0", port=8080, debug=False)


if __name__ == "__main__":
    print("=" * 60)
    print("  CorpAuth & CorpApp - OAuth 2.0 System")
    print("  OAuth Server: http://0.0.0.0:8443")
    print("  Client App:   http://0.0.0.0:8080")
    print("=" * 60)

    oauth_thread = threading.Thread(target=run_oauth_server, daemon=True)
    oauth_thread.start()

    run_client_app()
