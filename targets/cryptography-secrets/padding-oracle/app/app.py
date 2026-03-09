"""SecureAuth Token Service - Vulnerable Flask Application.

WARNING: This application is intentionally vulnerable (CWE-209, CWE-327).
         It leaks padding error information, enabling a padding oracle attack.
         DO NOT deploy this in any production environment.
"""

import json
import os

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from flask import Flask, jsonify, request, render_template_string, make_response, send_from_directory

app = Flask(__name__)
app.secret_key = "secureauth-internal-2024"

# AES key for token encryption (secret, not exposed)
AES_KEY = b"S3cur3Auth_K3y!!"  # 16 bytes


def encrypt_token(data_dict):
    """Encrypt a dictionary as JSON using AES-CBC."""
    plaintext = json.dumps(data_dict)
    cipher = AES.new(AES_KEY, AES.MODE_CBC)
    ct = cipher.encrypt(pad(plaintext.encode(), AES.block_size))
    return (cipher.iv + ct).hex()


def decrypt_token(hex_token):
    """Decrypt an AES-CBC token. Returns (data_dict, error_type).
    error_type: None=success, 'padding'=bad padding, 'format'=bad JSON
    """
    try:
        raw = bytes.fromhex(hex_token)
    except ValueError:
        return None, "format"

    if len(raw) < 32 or len(raw) % 16 != 0:
        return None, "format"

    iv = raw[:16]
    ct = raw[16:]

    cipher = AES.new(AES_KEY, AES.MODE_CBC, iv)
    try:
        plaintext = unpad(cipher.decrypt(ct), AES.block_size)
    except ValueError:
        # VULNERABILITY: This reveals that padding was invalid (CWE-209)
        return None, "padding"

    try:
        data = json.loads(plaintext.decode())
        return data, None
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None, "format"


# Pre-generate the admin token
ADMIN_TOKEN = encrypt_token({"user": "admin", "role": "admin"})


# ------------------------------------------------------------------
# Main Page
# ------------------------------------------------------------------
INDEX_HTML = """
<!DOCTYPE html>
<html>
<head><title>SecureAuth Token Service</title>
<style>
body { font-family: 'Consolas', monospace; margin: 0; background: #111; color: #ccc; }
.header { background: #1a1a1a; padding: 20px 40px; border-bottom: 2px solid #e74c3c; }
.header h1 { color: #e74c3c; margin: 0; }
.container { max-width: 900px; margin: 30px auto; padding: 20px; }
.card { background: #1a1a1a; padding: 20px; border-radius: 6px; border: 1px solid #333; margin: 15px 0; }
code { background: #000; padding: 2px 8px; border-radius: 3px; color: #2ecc71; }
a { color: #e74c3c; }
input { padding: 10px; margin: 5px; background: #222; border: 1px solid #444; color: #ccc; border-radius: 4px; }
button { padding: 10px 20px; background: #e74c3c; color: white; border: none; border-radius: 4px; cursor: pointer; }
.flag-box { background: #0d2818; padding: 15px; border-radius: 4px; border: 1px solid #2ecc71; font-family: monospace; margin: 10px 0; }
</style>
</head>
<body>
<div class="header"><h1>SecureAuth</h1><p>Encrypted Token Authentication Service</p></div>
<div class="container">
    <div class="card">
        <h3>Authentication</h3>
        <form method="POST" action="/api/login">
            <input type="text" name="username" placeholder="Username" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Get Token</button>
        </form>
    </div>
    <div class="card">
        <h3>API Endpoints</h3>
        <ul>
            <li><code>POST /api/login</code> - Get an encrypted auth token</li>
            <li><code>GET /api/verify?token=HEX</code> - Verify a token</li>
            <li><code>GET /api/admin-token</code> - View admin token (encrypted)</li>
            <li><code>GET /admin</code> - Admin panel (requires valid admin token as cookie)</li>
        </ul>
    </div>
    <div class="card">
        <p>Token Format: AES-128-CBC | hex(IV + ciphertext) | PKCS7 padding</p>
    </div>
</div>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(INDEX_HTML)


# ------------------------------------------------------------------
# Login - returns encrypted token
# ------------------------------------------------------------------
USERS = {
    "guest": {"password": "guest123", "role": "guest"},
    "user1": {"password": "user1pass", "role": "user"},
    "admin": {"password": "Adm1n_S3cur3!2024", "role": "admin"},
}


@app.route("/api/login", methods=["POST"])
def api_login():
    username = request.form.get("username") or (request.json or {}).get("username", "")
    password = request.form.get("password") or (request.json or {}).get("password", "")

    user = USERS.get(username)
    if user and user["password"] == password:
        token = encrypt_token({"user": username, "role": user["role"]})

        user_flag = "[not accessible]"
        try:
            with open("/home/webapp/user.txt") as f:
                user_flag = f.read().strip()
        except Exception:
            pass

        resp = make_response(jsonify({
            "status": "authenticated",
            "token": token,
            "user_flag": user_flag,
            "note": "Set this as your auth_token cookie to access protected endpoints.",
        }))
        resp.set_cookie("auth_token", token)
        return resp
    else:
        return jsonify({"error": "Invalid credentials"}), 401


# ------------------------------------------------------------------
# VULNERABILITY: Padding oracle via different error responses (CWE-209)
# ------------------------------------------------------------------
@app.route("/api/verify")
def api_verify():
    """Verify a token. VULNERABLE: Returns different errors for padding vs format issues."""
    token = request.args.get("token", "")
    if not token:
        return jsonify({"error": "No token provided"}), 400

    data, error_type = decrypt_token(token)

    if error_type == "padding":
        # VULNERABILITY: This distinct error message creates the padding oracle
        return jsonify({"error": "Invalid padding"}), 400
    elif error_type == "format":
        return jsonify({"error": "Invalid token format"}), 403
    else:
        return jsonify({
            "valid": True,
            "user": data.get("user"),
            "role": data.get("role"),
        })


# ------------------------------------------------------------------
# Admin token endpoint - shows the encrypted admin token to attack
# ------------------------------------------------------------------
@app.route("/api/admin-token")
def api_admin_token():
    """Expose the encrypted admin token for the attacker to target."""
    crypto_flag = "[not accessible]"
    try:
        with open("/opt/secureauth/crypto_flag.txt") as f:
            crypto_flag = f.read().strip()
    except Exception:
        pass

    return jsonify({
        "admin_token": ADMIN_TOKEN,
        "crypto_flag": crypto_flag,
        "hint": "This is the encrypted admin token. Can you decrypt it without the key?",
        "format": "hex(IV_16bytes + AES-CBC-ciphertext) with PKCS7 padding",
    })


# ------------------------------------------------------------------
# Admin panel - requires valid admin token
# ------------------------------------------------------------------
@app.route("/admin")
def admin_panel():
    token = request.cookies.get("auth_token", "")
    if not token:
        return "403 Forbidden - No auth token.", 403

    data, error_type = decrypt_token(token)
    if error_type or not data:
        return "403 Forbidden - Invalid token.", 403

    if data.get("role") != "admin":
        return "403 Forbidden - Admin role required.", 403

    root_flag = "[not accessible]"
    try:
        with open("/root/root.txt") as f:
            root_flag = f.read().strip()
    except Exception:
        root_flag = "[requires root - check /root/root.txt]"

    return render_template_string("""
    <!DOCTYPE html><html><head><title>Admin Panel</title>
    <style>body{font-family:monospace;margin:40px;background:#111;color:#ccc;}
    .flag-box{background:#0d2818;padding:15px;border-radius:4px;border:1px solid #2ecc71;font-family:monospace;margin:10px 0;}
    a{color:#e74c3c;}</style>
    </head><body>
    <h1>SecureAuth Admin Panel</h1>
    <p>Welcome, admin. Token successfully decrypted.</p>
    <div class="flag-box">Root Flag: {{ root_flag }}</div>
    <p><a href="/">Back</a></p>
    </body></html>
    """, root_flag=root_flag)


@app.route("/.secure/<path:filename>")
def serve_secure(filename):
    return send_from_directory("/var/www/html/.secure", filename)


@app.route("/robots.txt")
def robots():
    return "User-agent: *\nDisallow: /api/\nDisallow: /admin/\nDisallow: /.secure/\n", 200, {"Content-Type": "text/plain"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
