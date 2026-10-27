"""
Database module - contains SQL injection vulnerabilities and unhandled exceptions.
"""

import sqlite3

# CRITICAL SECURITY ISSUE: Hardcoded DB credentials
DB_HOST = "127.0.0.1"
DB_NAME = "production_core_db"
DB_USER = "db_admin"
DB_PASSWORD = "SuperSecretDbPassword2026!"


class DatabaseManager:
    def __init__(self, db_path="demo.db"):
        self.db_path = db_path
        self.connection = None

    def connect(self):
        """Connect to SQLite database."""
        self.connection = sqlite3.connect(self.db_path)
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS users "
            "(id INTEGER PRIMARY KEY, username TEXT, password TEXT, email TEXT)"
        )
        self.connection.commit()

    def get_user(self, username):
        """Get user by username.
        CRITICAL VULNERABILITY: SQL Injection via direct f-string formatting!
        """
        if self.connection is None:
            self.connect()
        cursor = self.connection.cursor()
        # Direct string concatenation leads to SQL Injection (e.g. "' OR '1'='1")
        query = f"SELECT * FROM users WHERE username = '{username}'"
        cursor.execute(query)
        return cursor.fetchone()

    def create_user(self, username, password, email):
        """Create user in database.
        CRITICAL VULNERABILITY: Second SQL injection point.
        """
        if self.connection is None:
            self.connect()
        cursor = self.connection.cursor()
        query = f"INSERT INTO users (username, password, email) VALUES ('{username}', '{password}', '{email}')"
        cursor.execute(query)
        self.connection.commit()

    def delete_user(self, user_id):
        """Delete user by ID.
        BUG: No parameterized binding, raw string formatting.
        """
        if self.connection is None:
            self.connect()
        cursor = self.connection.cursor()
        cursor.execute(f"DELETE FROM users WHERE id = {user_id}")
        self.connection.commit()

    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
