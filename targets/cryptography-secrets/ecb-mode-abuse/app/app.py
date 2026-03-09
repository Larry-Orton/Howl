"""PixelVault Profile Manager - Vulnerable Flask Application.

WARNING: This application is intentionally vulnerable (CWE-327).
         It uses AES-ECB mode which allows block manipulation attacks.
         DO NOT deploy this in any production environment.
"""

import json
import os

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from flask import Flask, jsonify, request, render_template_string, make_response, send_from_directory

app = Flask(__name__)
app.secret_key = "pixelvault-internal-2024"

# AES key (secret)
AES_KEY = b"P1x3lVault_K3y!!"  # 16 bytes


def ecb_encrypt(plaintext_bytes):
    """VULNERABLE: AES-ECB encryption (CWE-327).
    Each 16-byte block is encrypted independently.
    Identical plaintext blocks = identical ciphertext blocks.
    """
    cipher = AES.new(AES_KEY, AES.MODE_ECB)
    return cipher.encrypt(pad(plaintext_bytes, AES.block_size))


def ecb_decrypt(ciphertext_bytes):
    """Decrypt AES-ECB data."""
    cipher = AES.new(AES_KEY, AES.MODE_ECB)
    try:
        return unpad(cipher.decrypt(ciphertext_bytes), AES.block_size)
    except ValueError:
        return None


def create_profile_token(username, role="user"):
    """Create an encrypted profile token.
    Token plaintext format: {"user":"USERNAME","role":"ROLE"}
    """
    profile = json.dumps({"user": username, "role": role}, separators=(",", ":"))
    encrypted = ecb_encrypt(profile.encode())
    return encrypted.hex()


def decode_profile_token(hex_token):
    """Decode and verify a profile token."""
    try:
        raw = bytes.fromhex(hex_token)
    except ValueError:
        return None

    plaintext = ecb_decrypt(raw)
    if plaintext is None:
        return None

    try:
        data = json.loads(plaintext.decode())
        return data
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None


# ------------------------------------------------------------------
# Main Page
# ------------------------------------------------------------------
INDEX_HTML = """
<!DOCTYPE html>
<html>
<head><title>PixelVault - Profile Manager</title>
<style>
body { font-family: 'Segoe UI', sans-serif; margin: 0; background: #0f0f23; color: #cccccc; }
.header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px 40px; }
.header h1 { margin: 0; color: white; }
.container { max-width: 900px; margin: 30px auto; padding: 20px; }
.card { background: #1a1a2e; padding: 25px; border-radius: 8px; border: 1px solid #333; margin: 15px 0; }
code { background: #0f0f23; padding: 2px 8px; border-radius: 3px; color: #a78bfa; }
a { color: #a78bfa; }
input { padding: 10px; margin: 5px; background: #16162a; border: 1px solid #444; color: #ccc; border-radius: 4px; width: 300px; }
button { padding: 10px 20px; background: #7c3aed; color: white; border: none; border-radius: 4px; cursor: pointer; }
.token-display { background: #0f0f23; padding: 15px; border-radius: 4px; font-family: monospace; font-size: 0.85em; word-break: break-all; border: 1px solid #333; margin: 10px 0; }
.flag-box { background: #0d2818; padding: 15px; border-radius: 4px; border: 1px solid #22c55e; font-family: monospace; margin: 10px 0; }
</style>
</head>
<body>
<div class="header"><h1>PixelVault</h1><p>Encrypted Profile Management</p></div>
<div class="container">
    <div class="card">
        <h3>Create Profile</h3>
        <form method="POST" action="/api/profile/create">
            <input type="text" name="username" placeholder="Choose a username" required>
            <button type="submit">Create Profile</button>
        </form>
    </div>
    <div class="card">
        <h3>API Endpoints</h3>
        <ul>
            <li><code>POST /api/profile/create</code> - Create profile (returns encrypted token)</li>
            <li><code>GET /api/profile/view</code> - View profile (uses profile_token cookie)</li>
            <li><code>GET /api/profile/info</code> - Token format information</li>
            <li><code>GET /admin</code> - Admin panel (requires admin role in token)</li>
        </ul>
    </div>
</div>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(INDEX_HTML)


# ------------------------------------------------------------------
# Profile API
# ------------------------------------------------------------------
@app.route("/api/profile/create", methods=["POST"])
def create_profile():
    username = request.form.get("username") or (request.json or {}).get("username", "")
    if not username:
        return jsonify({"error": "Username required"}), 400

    # Always create with role=user
    token = create_profile_token(username, "user")

    user_flag = "[not accessible]"
    try:
        with open("/home/webapp/user.txt") as f:
            user_flag = f.read().strip()
    except Exception:
        pass

    resp = make_response(jsonify({
        "status": "created",
        "username": username,
        "role": "user",
        "token": token,
        "token_length": len(token),
        "blocks": len(token) // 32,
        "user_flag": user_flag,
        "note": "Set this as your profile_token cookie.",
    }))
    resp.set_cookie("profile_token", token)
    return resp


@app.route("/api/profile/view")
def view_profile():
    token = request.cookies.get("profile_token") or request.args.get("token", "")
    if not token:
        return jsonify({"error": "No profile token. Create a profile first."}), 400

    profile = decode_profile_token(token)
    if profile is None:
        return jsonify({"error": "Invalid or corrupted token."}), 400

    # Show block-level breakdown of the token
    blocks = [token[i:i+32] for i in range(0, len(token), 32)]

    crypto_flag = "[not accessible]"
    try:
        with open("/opt/pixelvault/crypto_flag.txt") as f:
            crypto_flag = f.read().strip()
    except Exception:
        pass

    return jsonify({
        "profile": profile,
        "crypto_flag": crypto_flag,
        "token_info": {
            "hex": token,
            "blocks": blocks,
            "num_blocks": len(blocks),
            "block_size": 16,
        },
    })


@app.route("/api/profile/info")
def profile_info():
    """Expose token format details."""
    return jsonify({
        "encryption": "AES-128-ECB",
        "block_size": 16,
        "padding": "PKCS7",
        "token_format": '{"user":"USERNAME","role":"ROLE"}',
        "note": "Each 16-byte block is encrypted independently. No IV is used.",
        "example_layout": {
            "block_0": '{"user":"abcdef",',
            "block_1": '"role":"user"}+pad',
            "note": "Block boundaries depend on username length",
        },
    })


# ------------------------------------------------------------------
# Admin Panel
# ------------------------------------------------------------------
@app.route("/admin")
def admin_panel():
    token = request.cookies.get("profile_token", "")
    if not token:
        return "403 Forbidden - No profile token.", 403

    profile = decode_profile_token(token)
    if profile is None:
        return "403 Forbidden - Invalid token.", 403

    if profile.get("role") != "admin":
        return f"403 Forbidden - Your role is '{profile.get('role')}', admin required.", 403

    root_flag = "[not accessible]"
    try:
        with open("/root/root.txt") as f:
            root_flag = f.read().strip()
    except Exception:
        root_flag = "[requires root - check /root/root.txt]"

    return render_template_string("""
    <!DOCTYPE html><html><head><title>Admin Panel</title>
    <style>body{font-family:monospace;margin:40px;background:#0f0f23;color:#ccc;}
    .flag-box{background:#0d2818;padding:15px;border-radius:4px;border:1px solid #22c55e;font-family:monospace;margin:10px 0;}
    a{color:#a78bfa;}</style>
    </head><body>
    <h1>PixelVault Admin Panel</h1>
    <p>Welcome, admin! Token role verified: {{ profile.role }}</p>
    <div class="flag-box">Root Flag: {{ root_flag }}</div>
    <p>Profile: {{ profile }}</p>
    <p><a href="/">Back</a></p>
    </body></html>
    """, root_flag=root_flag, profile=profile)


@app.route("/.vault/<path:filename>")
def serve_vault(filename):
    return send_from_directory("/var/www/html/.vault", filename)


@app.route("/robots.txt")
def robots():
    return "User-agent: *\nDisallow: /api/\nDisallow: /admin/\nDisallow: /.vault/\n", 200, {"Content-Type": "text/plain"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
