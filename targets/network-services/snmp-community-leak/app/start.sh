#!/bin/bash
# Start all services for snmp-community-leak target

# Start SSH
/usr/sbin/sshd

# Start SNMP daemon
snmpd -f -Lo -C -c /etc/snmp/snmpd.conf &

# Start fake monitoring agent (visible in process list with creds)
/opt/sentinel/netmon_agent.sh &

# Start web status page (foreground to keep container alive)
python3 /app/status_page.py
