#!/usr/bin/env python3
"""Vaultline Systems - Simple status page on port 8080."""

import http.server
import socketserver

HTML = """<!DOCTYPE html>
<html>
<head><title>Vaultline Systems - Status</title></head>
<body>
<h1>Vaultline Systems</h1>
<p>All services operational.</p>
<p>FTP Archive: <span style="color:green">ONLINE</span></p>
<p>SSH Gateway: <span style="color:green">ONLINE</span></p>
<!-- Internal note: status flags stored at /.status/ -->
<!-- TODO: remove debug path before production -->
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
        pass  # Suppress logs

if __name__ == "__main__":
    with socketserver.TCPServer(("0.0.0.0", 8080), Handler) as httpd:
        httpd.serve_forever()
