#!/bin/bash
# Start all services for vpn-gateway-bypass target

# Start internal admin panel (simulates internal network service)
python3 /app/internal_admin.py &

# Start VPN web portal on 443 (foreground to keep container alive)
python3 /app/portal.py
