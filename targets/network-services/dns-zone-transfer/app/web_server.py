#!/usr/bin/env python3
"""Prism Networks - Web server with virtual host routing."""

import http.server
import socketserver
import os

PUBLIC_HTML = """<!DOCTYPE html>
<html>
<head><title>Prism Networks</title></head>
<body>
<h1>Prism Networks</h1>
<p>Welcome to Prism Networks - prismnet.local</p>
<p>Our DNS infrastructure manages the prismnet.local domain.</p>
<p>Services: Mail, VPN, Web Hosting</p>
<!-- TODO: clean up .config directory before going live -->
</body>
</html>
"""

SECRET_ADMIN_HTML = """<!DOCTYPE html>
<html>
<head><title>Secret Admin Panel</title></head>
<body>
<h1>Prism Networks - Internal Administration</h1>
<p>This panel is for authorized administrators only.</p>
<p><a href="/flag">View System Flag</a></p>
</body>
</html>
"""


class VHostHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        host = self.headers.get("Host", "")

        if "secret-admin" in host:
            if self.path == "/flag":
                try:
                    flag = open("/var/www/secret-admin/root.txt").read().strip()
                    content = f"<html><body><h1>Flag</h1><pre>{flag}</pre></body></html>"
                except FileNotFoundError:
                    content = "<html><body><p>Flag file not found.</p></body></html>"
            else:
                content = SECRET_ADMIN_HTML
        else:
            content = PUBLIC_HTML

        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(content.encode())

    def log_message(self, format, *args):
        pass


if __name__ == "__main__":
    with socketserver.TCPServer(("0.0.0.0", 8080), VHostHandler) as httpd:
        httpd.serve_forever()
