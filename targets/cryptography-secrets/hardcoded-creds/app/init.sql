-- Initial MySQL setup for hardcoded-creds target
-- The init_db.py script handles detailed table creation and data insertion.
-- This file ensures the database exists.

CREATE DATABASE IF NOT EXISTS inventory;
GRANT ALL PRIVILEGES ON inventory.* TO 'inventory_admin'@'%';
FLUSH PRIVILEGES;
