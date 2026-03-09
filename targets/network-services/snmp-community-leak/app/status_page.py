#!/usr/bin/env python3
"""Sentinel Networking - Device Status Page."""

import http.server
import socketserver

HTML = """<!DOCTYPE html>
<html>
<head><title>Sentinel SG-500 Status</title></head>
<body style="font-family: Arial; background: #0d1117; color: #c9d1d9;">
<h1>Sentinel SG-500 Security Gateway</h1>
<hr style="border-color: #30363d;">
<h2>Device Status</h2>
<table style="border-collapse: collapse;">
<tr><td style="padding: 4px 12px;">Hostname:</td><td>sentinel-gw-01</td></tr>
<tr><td style="padding: 4px 12px;">Firmware:</td><td>v4.2.1-stable</td></tr>
<tr><td style="padding: 4px 12px;">SNMP:</td><td style="color: #3fb950;">Active (UDP 161)</td></tr>
<tr><td style="padding: 4px 12px;">SSH:</td><td style="color: #3fb950;">Active (TCP 22)</td></tr>
<tr><td style="padding: 4px 12px;">Monitoring:</td><td style="color: #3fb950;">netmon_agent running</td></tr>
</table>
<hr style="border-color: #30363d;">
<p style="color: #8b949e;">SNMP monitoring enabled with default community string for NOC access.</p>
<p style="color: #8b949e;"><small>Sentinel Networking &copy; 2024</small></p>
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
