#!/bin/bash
# Start all services for telnet-default-creds target

# Start xinetd (provides telnet)
xinetd -stayalive &

# Start web dashboard (foreground to keep container alive)
python3 /app/dashboard.py
