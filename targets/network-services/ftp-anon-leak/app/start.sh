#!/bin/bash
# Start all services for ftp-anon-leak target

# Start SSH
/usr/sbin/sshd

# Start vsftpd in background
vsftpd /etc/vsftpd.conf &

# Start status page (foreground to keep container alive)
python3 /app/status_page.py
