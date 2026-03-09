"""Initialize the MySQL database with users using MD5 password hashes."""

import hashlib
import time

import mysql.connector


def md5_hash(password):
    return hashlib.md5(password.encode()).hexdigest()


def initialize():
    for attempt in range(30):
        try:
            conn = mysql.connector.connect(
                host="mysql",
                port=3306,
                user="cs_app",
                password="cs_db_p@ss2024",
                database="cipherstack",
            )
            break
        except mysql.connector.Error:
            time.sleep(2)
    else:
        print("Could not connect to MySQL after 30 attempts")
        return

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100) NOT NULL UNIQUE,
            email VARCHAR(200) NOT NULL,
            password_hash VARCHAR(64) NOT NULL,
            role VARCHAR(50) DEFAULT 'user'
        )
    """)

    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        # Passwords chosen to be in rockyou.txt / common password lists
        users = [
            ("admin", "admin@cipherstack.local", md5_hash("trustno1"), "admin"),
            ("jdoe", "john.doe@cipherstack.local", md5_hash("password123"), "user"),
            ("asmith", "alice.smith@cipherstack.local", md5_hash("letmein"), "user"),
            ("bwilson", "bob.wilson@cipherstack.local", md5_hash("dragon"), "user"),
            ("cjones", "carol.jones@cipherstack.local", md5_hash("monkey"), "moderator"),
        ]
        cursor.executemany(
            "INSERT INTO users (username, email, password_hash, role) VALUES (%s, %s, %s, %s)",
            users,
        )

    conn.commit()
    cursor.close()
    conn.close()
    print("Database initialized with MD5-hashed passwords.")


if __name__ == "__main__":
    initialize()
