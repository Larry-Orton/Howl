"""OpenLedger Corp - Financial Application (leaks credentials via backup endpoint)."""

from flask import Flask

app = Flask(__name__)


@app.route("/")
def index():
    """Main financial dashboard."""
    return """<!DOCTYPE html>
<html>
<head><title>OpenLedger Corp - Financial Portal</title></head>
<body>
<h1>OpenLedger Corp</h1>
<h2>Financial Data Portal</h2>
<ul>
  <li><a href="/transactions">Recent Transactions</a></li>
  <li><a href="/reports">Reports</a></li>
  <li><a href="/audit">Audit Log</a></li>
</ul>
</body>
</html>"""


@app.route("/transactions")
def transactions():
    """Transaction listing."""
    return """<!DOCTYPE html>
<html>
<head><title>OpenLedger - Transactions</title></head>
<body>
<h1>Recent Transactions</h1>
<table border="1" cellpadding="8">
  <tr><th>Date</th><th>Description</th><th>Amount</th></tr>
  <tr><td>2024-03-08</td><td>Wire Transfer - Acme Corp</td><td>$12,500</td></tr>
  <tr><td>2024-03-07</td><td>Invoice Payment - TechStart</td><td>$8,750</td></tr>
  <tr><td>2024-03-06</td><td>Payroll Processing</td><td>$45,000</td></tr>
</table>
<p><a href="/">Back</a></p>
</body>
</html>"""


@app.route("/reports")
def reports():
    """Reports page."""
    return """<!DOCTYPE html>
<html>
<head><title>OpenLedger - Reports</title></head>
<body>
<h1>Reports</h1>
<p>Q1 2024 Financial Summary: <em>In Progress</em></p>
<p>Annual Audit Report: <em>Pending</em></p>
<p><a href="/">Back</a></p>
</body>
</html>"""


@app.route("/audit")
def audit():
    """Audit log."""
    return """<!DOCTYPE html>
<html>
<head><title>OpenLedger - Audit</title></head>
<body>
<h1>Audit Log</h1>
<pre>
[2024-03-08 10:15] User 'admin' logged in
[2024-03-08 09:00] Backup job completed
[2024-03-07 23:45] Server migration completed - CHECK FILE PERMISSIONS
[2024-03-07 18:30] User 'ledger' created
</pre>
<p><a href="/">Back</a></p>
</body>
</html>"""


@app.route("/backup")
def backup():
    """Backup endpoint - VULNERABLE: exposes credentials."""
    return """<!DOCTYPE html>
<html>
<head><title>OpenLedger - Backup</title></head>
<body>
<h1>Database Backup Export</h1>
<p style="color:red">WARNING: This endpoint should be restricted!</p>
<h3>System Configuration Backup</h3>
<pre>
-- OpenLedger System Configuration Dump --
-- Generated: 2024-03-08 --

[SSH Access]
Username: ledger
Password: 0p3nL3dg3r_2024
Port: 22
Note: Service account for ledger application

[Migration Notes]
- Server migrated on 2024-03-07
- File permissions need to be reviewed post-migration
- /etc/passwd permissions may have been affected
</pre>
<!-- Debug: recon flag at /var/www/.config/recon_flag.txt -->
<p><a href="/">Back</a></p>
</body>
</html>"""


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
