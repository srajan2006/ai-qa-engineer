"""
User service - intentionally contains security vulnerabilities and logic bugs.
"""

import hashlib

# CRITICAL SECURITY ISSUE: Hardcoded secrets in source code
SECRET_KEY = "my_super_secret_jwt_key_2026"
API_KEY = "sk-prod-a1b2c3d4e5f6g7h8i9j0"


class UserService:
    def __init__(self):
        self.users = {}
        self.admin_password = "admin_master_password_123"

    def create_user(self, username, password, email):
        """Create a new user.
        CRITICAL BUG: Password stored in plaintext!
        """
        user = {
            "username": username,
            "password": password,  # Plaintext password storage
            "email": email,
            "role": "user",
        }
        self.users[username] = user
        return user

    def authenticate(self, username, password):
        """Authenticate a user.
        BUG: Missing None check on user lookup + plaintext comparison.
        """
        user = self.users.get(username)
        if user is None:
            return False
        if user["password"] == password:
            return True
        return False

    def get_user_data(self, username):
        """Get user data.
        BUG: Missing authorization check. Any caller can access any user's profile.
        """
        return self.users.get(username)

    def update_email(self, username, new_email):
        """Update user email.
        BUG: Incomplete return paths and missing email format validation.
        """
        if username in self.users:
            self.users[username]["email"] = new_email
            return True
        # Implicitly returns None instead of False

    def delete_user(self, username):
        """Delete user.
        BUG: Missing permission/admin role check.
        """
        if username in self.users:
            del self.users[username]
            return True
        return False

    def hash_password_weak(self, password):
        """Hash password using MD5.
        SECURITY ISSUE: MD5 is cryptographically weak and deprecated for passwords.
        """
        return hashlib.md5(password.encode()).hexdigest()
