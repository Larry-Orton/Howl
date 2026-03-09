"""IronGate Security - Dual HTTPS Service Application.

WARNING: This application is intentionally vulnerable (CWE-321).
         The TLS private key is exposed through a debug endpoint.
         DO NOT deploy this in any production environment.
"""

import base64
import json
import os
import ssl
import subprocess
import threading

from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from flask import Flask, jsonify, request, render_template_string, make_response, send_from_directory

CERT_DIR = "/app/certs"
CERT_FILE = os.path.join(CERT_DIR, "server.crt")
KEY_FILE = os.path.join(CERT_DIR, "server.key")

# Root admin credentials (encrypted and sent via internal API)
ROOT_ADMIN_USER = "irongate_root"
ROOT_ADMIN_PASS = "Ir0nG@te_R00t!2024"


def get_rsa_key():
    """Load the RSA private key for encryption operations."""
    try:
        with open(KEY_FILE, "r") as f:
            return RSA.import_key(f.read())
    except Exception:
        return None


def encrypt_credentials():
    """Encrypt the root credentials using the RSA public key."""
    key = get_rsa_key()
    if not key:
        return None

    creds = json.dumps({"username": ROOT_ADMIN_USER, "password": ROOT_ADMIN_PASS})
    public_key = key.publickey()
    cipher = PKCS1_OAEP.new(public_key)
    encrypted = cipher.encrypt(creds.encode())
    return base64.b64encode(encrypted).decode()


# ======================================================================
# SERVICE A: Public Portal (port 443)
# ======================================================================
public_app = Flask("public")
public_app.secret_key = "irongate-public-2024"

PUBLIC_INDEX = """
<!DOCTYPE html>
<html>
<head><title>IronGate Security</title>
<style>
body { font-family: 'Segoe UI', sans-serif; margin: 0; background: #0a0a0a; color: #d4d4d4; }
.header { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); padding: 30px 40px; border-bottom: 3px solid #e63946; }
.header h1 { color: #e63946; margin: 0; font-size: 2em; }
.header p { color: #888; }
.container { max-width: 900px; margin: 30px auto; padding: 20px; }
.card { background: #1a1a1a; padding: 25px; border-radius: 8px; border: 1px solid #333; margin: 15px 0; }
a { color: #e63946; }
.badge { display: inline-block; background: #e63946; color: white; padding: 3px 10px; border-radius: 12px; font-size: 0.75em; }
.lock { color: #22c55e; }
input { padding: 10px; margin: 5px; background: #111; border: 1px solid #333; color: #ccc; border-radius: 4px; }
button { padding: 10px 20px; background: #e63946; color: white; border: none; border-radius: 4px; cursor: pointer; }
.flag-box { background: #0d2818; padding: 15px; border-radius: 4px; border: 1px solid #22c55e; font-family: monospace; }
</style>
</head>
<body>
<div class="header">
    <h1>IronGate Security</h1>
    <p>Enterprise Security Solutions | <span class="lock">HTTPS Secured</span></p>
</div>
<div class="container">
    <div class="card">
        <h2>Welcome to IronGate</h2>
        <p>We provide enterprise-grade security solutions including:</p>
        <ul>
            <li>Network Security Assessment</li>
            <li>Penetration Testing</li>
            <li>Compliance Auditing</li>
            <li>Incident Response</li>
        </ul>
    </div>
    <div class="card">
        <h3>TLS Certificate Information</h3>
        <p>This connection is secured with TLS. <span class="badge">Self-Signed</span></p>
        <p><a href="/cert-info">View Certificate Details</a></p>
    </div>
    <div class="card">
        <h3>Client Portal</h3>
        <p><a href="/admin/root">Root Administration</a> (Authorized personnel only)</p>
    </div>
    <p style="color: #444; margin-top: 30px;">IronGate Security v4.2.0 | Internal Management: port 8443</p>
</div>
</body>
</html>
"""


@public_app.route("/")
def pub_index():
    return render_template_string(PUBLIC_INDEX)


@public_app.route("/cert-info")
def cert_info():
    """Show certificate details."""
    cert_flag = "[not accessible]"
    try:
        with open("/opt/irongate/cert_flag.txt") as f:
            cert_flag = f.read().strip()
    except Exception:
        pass

    cert_text = ""
    try:
        result = subprocess.run(
            ["openssl", "x509", "-in", CERT_FILE, "-text", "-noout"],
            capture_output=True, text=True
        )
        cert_text = result.stdout
    except Exception:
        cert_text = "[Certificate not available]"

    return render_template_string("""
    <!DOCTYPE html><html><head><title>Certificate Info</title>
    <style>body{font-family:monospace;margin:40px;background:#0a0a0a;color:#d4d4d4;}
    pre{background:#111;padding:20px;border-radius:6px;border:1px solid #333;overflow-x:auto;}
    .flag-box{background:#0d2818;padding:15px;border-radius:4px;border:1px solid #22c55e;font-family:monospace;margin:10px 0;}
    a{color:#e63946;}</style>
    </head><body>
    <h1>TLS Certificate Details</h1>
    <div class="flag-box">Cert Analysis Flag: {{ cert_flag }}</div>
    <pre>{{ cert_text }}</pre>
    <p><a href="/">Back</a></p>
    </body></html>
    """, cert_text=cert_text, cert_flag=cert_flag)


@public_app.route("/admin/root", methods=["GET", "POST"])
def admin_root():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        if username == ROOT_ADMIN_USER and password == ROOT_ADMIN_PASS:
            root_flag = "[not accessible]"
            try:
                with open("/root/root.txt") as f:
                    root_flag = f.read().strip()
            except Exception:
                root_flag = "[requires root - check /root/root.txt]"

            return render_template_string("""
            <!DOCTYPE html><html><head><title>Root Admin</title>
            <style>body{font-family:monospace;margin:40px;background:#0a0a0a;color:#d4d4d4;}
            .flag-box{background:#0d2818;padding:15px;border-radius:4px;border:1px solid #22c55e;font-family:monospace;margin:10px 0;}
            a{color:#e63946;}</style>
            </head><body>
            <h1>IronGate Root Administration</h1>
            <p>Welcome, root administrator.</p>
            <div class="flag-box">Root Flag: {{ root_flag }}</div>
            <p><a href="/">Back</a></p>
            </body></html>
            """, root_flag=root_flag)
        else:
            return render_template_string("""
            <!DOCTYPE html><html><head><title>Root Login</title>
            <style>body{font-family:monospace;background:#0a0a0a;color:#d4d4d4;display:flex;justify-content:center;align-items:center;height:100vh;margin:0;}
            .box{background:#1a1a1a;padding:40px;border-radius:8px;border:1px solid #333;width:350px;}
            h2{color:#e63946;text-align:center;} input{width:100%;padding:10px;margin:8px 0;background:#111;border:1px solid #333;color:#ccc;border-radius:4px;box-sizing:border-box;}
            button{width:100%;padding:10px;background:#e63946;color:white;border:none;border-radius:4px;cursor:pointer;}
            .error{color:#e63946;text-align:center;}</style>
            </head><body><div class="box">
            <h2>Root Login</h2><p class="error">Invalid credentials.</p>
            <form method="POST"><input type="text" name="username" placeholder="Root Username" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Authenticate</button></form>
            </div></body></html>
            """)

    return render_template_string("""
    <!DOCTYPE html><html><head><title>Root Login</title>
    <style>body{font-family:monospace;background:#0a0a0a;color:#d4d4d4;display:flex;justify-content:center;align-items:center;height:100vh;margin:0;}
    .box{background:#1a1a1a;padding:40px;border-radius:8px;border:1px solid #333;width:350px;}
    h2{color:#e63946;text-align:center;} input{width:100%;padding:10px;margin:8px 0;background:#111;border:1px solid #333;color:#ccc;border-radius:4px;box-sizing:border-box;}
    button{width:100%;padding:10px;background:#e63946;color:white;border:none;border-radius:4px;cursor:pointer;}</style>
    </head><body><div class="box">
    <h2>Root Administration</h2>
    <form method="POST"><input type="text" name="username" placeholder="Root Username" required>
    <input type="password" name="password" placeholder="Password" required>
    <button type="submit">Authenticate</button></form>
    </div></body></html>
    """)


@public_app.route("/.irongate/<path:filename>")
def pub_serve_irongate(filename):
    return send_from_directory("/var/www/html/.irongate", filename)


@public_app.route("/robots.txt")
def pub_robots():
    return "User-agent: *\nDisallow: /admin/\nDisallow: /.irongate/\n", 200, {"Content-Type": "text/plain"}


# ======================================================================
# SERVICE B: Management API (port 8443)
# ======================================================================
mgmt_app = Flask("management")
mgmt_app.secret_key = "irongate-mgmt-2024"

MGMT_INDEX = """
<!DOCTYPE html>
<html>
<head><title>IronGate Management API</title>
<style>
body { font-family: monospace; margin: 0; background: #0d1117; color: #c9d1d9; }
.header { background: #161b22; padding: 20px 40px; border-bottom: 2px solid #f0883e; }
.header h1 { color: #f0883e; margin: 0; }
.container { max-width: 800px; margin: 30px auto; padding: 20px; }
.card { background: #161b22; padding: 20px; border-radius: 6px; border: 1px solid #30363d; margin: 15px 0; }
code { background: #0d1117; padding: 2px 8px; border-radius: 3px; color: #7ee787; }
a { color: #f0883e; }
.warning { color: #f0883e; background: #2d1b00; padding: 10px; border-radius: 4px; border: 1px solid #f0883e; }
</style>
</head>
<body>
<div class="header"><h1>IronGate Management API</h1><p>Internal Use Only</p></div>
<div class="container">
    <div class="card warning">
        WARNING: This is an internal management interface. Unauthorized access is prohibited.
    </div>
    <div class="card">
        <h3>API Endpoints</h3>
        <ul>
            <li><code>GET /api/health</code> - Service health check</li>
            <li><code>GET /api/services</code> - List managed services</li>
            <li><code>GET /api/internal/credential-exchange</code> - Internal credential sync</li>
        </ul>
    </div>
</div>
</body>
</html>
"""


@mgmt_app.route("/")
def mgmt_index():
    return render_template_string(MGMT_INDEX)


@mgmt_app.route("/api/health")
def mgmt_health():
    return jsonify({"status": "healthy", "service": "management-api", "version": "3.1.0"})


@mgmt_app.route("/api/services")
def mgmt_services():
    return jsonify({
        "services": [
            {"name": "public-portal", "port": 443, "tls": True, "status": "running"},
            {"name": "management-api", "port": 8443, "tls": True, "status": "running"},
        ],
        "tls_config": {
            "cert_file": "/app/certs/server.crt",
            "key_file": "/app/certs/server.key",
            "protocol": "TLSv1.2+",
        }
    })


# ------------------------------------------------------------------
# VULNERABILITY: Debug endpoint exposes the private key (CWE-321)
# ------------------------------------------------------------------
@mgmt_app.route("/debug/private-key")
def debug_private_key():
    """Debug endpoint that exposes the TLS private key."""
    user_flag = "[not accessible]"
    try:
        with open("/home/webapp/user.txt") as f:
            user_flag = f.read().strip()
    except Exception:
        pass

    try:
        with open(KEY_FILE, "r") as f:
            private_key = f.read()
    except Exception:
        private_key = "[key file not found]"

    return jsonify({
        "warning": "DEBUG ENDPOINT - REMOVE IN PRODUCTION",
        "user_flag": user_flag,
        "private_key": private_key,
        "key_file": KEY_FILE,
        "format": "PEM RSA 2048-bit",
    })


@mgmt_app.route("/debug/certs")
def debug_certs():
    """Debug endpoint listing certificate files."""
    try:
        cert_files = os.listdir(CERT_DIR)
    except Exception:
        cert_files = []

    return jsonify({
        "cert_directory": CERT_DIR,
        "files": cert_files,
        "endpoints": {
            "private_key": "/debug/private-key",
            "certificate": "/debug/certificate",
        }
    })


@mgmt_app.route("/debug/certificate")
def debug_certificate():
    """Show the public certificate."""
    try:
        with open(CERT_FILE, "r") as f:
            cert = f.read()
    except Exception:
        cert = "[cert file not found]"

    return jsonify({"certificate": cert, "format": "PEM X.509"})


# ------------------------------------------------------------------
# Internal credential exchange (encrypted with RSA public key)
# ------------------------------------------------------------------
@mgmt_app.route("/api/internal/credential-exchange")
def credential_exchange():
    """Simulates internal credential exchange using RSA encryption."""
    encrypted_creds = encrypt_credentials()
    if not encrypted_creds:
        return jsonify({"error": "Encryption not available"}), 500

    decrypt_flag = "[not accessible]"
    try:
        with open("/opt/irongate/decrypt_flag.txt") as f:
            decrypt_flag = f.read().strip()
    except Exception:
        pass

    return jsonify({
        "exchange_type": "credential_sync",
        "encryption": "RSA-OAEP",
        "encrypted_credentials": encrypted_creds,
        "decrypt_flag": decrypt_flag,
        "note": "Encrypted with the server's RSA public key. Requires private key to decrypt.",
        "format": "base64(RSA-OAEP(JSON({username, password})))",
    })


def run_public():
    """Run the public portal on port 443 with TLS."""
    # Wait for certs to be generated
    import time
    for _ in range(30):
        if os.path.exists(CERT_FILE) and os.path.exists(KEY_FILE):
            break
        time.sleep(1)

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(CERT_FILE, KEY_FILE)
    public_app.run(host="0.0.0.0", port=443, ssl_context=context, debug=False)


def run_management():
    """Run the management API on port 8443 with TLS."""
    import time
    for _ in range(30):
        if os.path.exists(CERT_FILE) and os.path.exists(KEY_FILE):
            break
        time.sleep(1)

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(CERT_FILE, KEY_FILE)
    mgmt_app.run(host="0.0.0.0", port=8443, ssl_context=context, debug=False)


if __name__ == "__main__":
    # Generate certs if they don't exist
    if not os.path.exists(CERT_FILE) or not os.path.exists(KEY_FILE):
        os.system("bash /app/init_certs.sh")

    # Run both services
    t1 = threading.Thread(target=run_public, daemon=True)
    t2 = threading.Thread(target=run_management, daemon=True)
    t1.start()
    t2.start()
    t1.join()
    t2.join()
