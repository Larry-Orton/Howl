#!/bin/bash
# Start all services for redis-unauth-rce target

# Start SSH
/usr/sbin/sshd

# Start Redis in background
redis-server /etc/redis/redis.conf &

# Wait for Redis to start, then seed data
sleep 2
python3 /var/www/app/init_redis.py

# Start web app (foreground to keep container alive)
python3 /var/www/app/webapp.py
