#!/bin/bash
# Start all services for cron-job-abuse target

# Start SSH
/usr/sbin/sshd

# Start cron daemon
cron

# Start web application (foreground to keep container alive)
python3 /var/www/app/app.py
