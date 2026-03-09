#!/bin/bash
# Start all services for dns-zone-transfer target

# Start SSH
/usr/sbin/sshd

# Start BIND9
named -g -u bind &

# Start web server (foreground to keep container alive)
python3 /app/web_server.py
