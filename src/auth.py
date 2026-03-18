import json
import os
import hashlib
from typing import Optional

USERS_FILE = "users.json"

def _hash_pw(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def init_users_db() -> bool:
    """Creates the file if missing. Returns True if DB exists."""
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w') as f:
            json.dump({}, f)
        return False
    return True

def create_user(username: str, password: str) -> tuple[bool, str]:
    init_users_db()
    with open(USERS_FILE, 'r') as f:
        users = json.load(f)
        
    if username in users:
        return False, "Username already exists."
        
    users[username] = {"password_hash": _hash_pw(password)}
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)
    return True, "User created successfully."

def authenticate(username: str, password: str) -> bool:
    if not os.path.exists(USERS_FILE):
        return False
    with open(USERS_FILE, 'r') as f:
        users = json.load(f)
        
    if username in users and users[username]["password_hash"] == _hash_pw(password):
        return True
    return False

def users_exist() -> bool:
    if not os.path.exists(USERS_FILE):
        return False
    with open(USERS_FILE, 'r') as f:
        users = json.load(f)
    return len(users) > 0
