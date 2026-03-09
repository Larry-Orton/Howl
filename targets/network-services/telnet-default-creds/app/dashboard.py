#!/usr/bin/env python3
"""GridIron GX-3000 - Device Web Dashboard."""

import http.server
import socketserver

HTML = """<!DOCTYPE html>
<html>
<head><title>GridIron GX-3000 Dashboard</title></head>
<body style="font-family: monospace; background: #1a1a2e; color: #0f0;">
<h1>GridIron GX-3000 Industrial Controller</h1>
<hr>
<table>
<tr><td>Model:</td><td>GX-3000</td></tr>
<tr><td>Firmware:</td><td>v2.4.1</td></tr>
<tr><td>Serial:</td><td>GX3K-2024-00847</td></tr>
<tr><td>Uptime:</td><td>47 days, 12:33:07</td></tr>
<tr><td>Status:</td><td style="color: lime;">OPERATIONAL</td></tr>
<tr><td>Telnet Mgmt:</td><td>Port 23 (Active)</td></tr>
</table>
<hr>
<p>For support contact: support@gridiron-industrial.com</p>
<!-- GridIron GX-3000 default management credentials: operator / Gr1dIr0n -->
<!-- Remember to change defaults after deployment! Ref: GX3K-SETUP-GUIDE -->
</body>
</html>
"""

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(HTML.encode())

    def log_message(self, format, *args):
        pass

if __name__ == "__main__":
    with socketserver.TCPServer(("0.0.0.0", 8080), Handler) as httpd:
        httpd.serve_forever()
