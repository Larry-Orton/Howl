#!/bin/bash
# Start all services for sudo-misconfig target

# Start SSH
/usr/sbin/sshd

# Start web application (foreground to keep container alive)
python3 /var/www/app/app.py
