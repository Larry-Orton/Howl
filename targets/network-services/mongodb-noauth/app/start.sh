#!/bin/bash
# Start all services for mongodb-noauth target

# Start MongoDB in background
mongod --config /etc/mongod.conf --fork --logpath /var/log/mongodb/mongod.log

# Wait for MongoDB to start, then seed data
sleep 3
python3 /app/init_mongo.py

# Start web app (foreground to keep container alive)
python3 /app/webapp.py
