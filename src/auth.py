import hashlib
from typing import Optional
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.github_storage import read_json_db, write_json_db

USERS_FILE = "users.json"

def _hash_pw(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username: str, password: str) -> tuple[bool, str]:
    pw_hash = _hash_pw(password)
    users, sha = read_json_db(USERS_FILE, default_val={})
    
    if username in users:
        return False, "Username already exists."
        
    users[username] = {"password_hash": pw_hash}
    write_json_db(USERS_FILE, users, sha)
    return True, "Cloud user created securely."

def authenticate(username: str, password: str) -> bool:
    pw_hash = _hash_pw(password)
    users, _ = read_json_db(USERS_FILE, default_val={})
    
    if username in users and users[username]["password_hash"] == pw_hash:
        return True
    return False

def users_exist() -> bool:
    users, _ = read_json_db(USERS_FILE, default_val={})
    return len(users) > 0

def get_all_users() -> list:
    users, _ = read_json_db(USERS_FILE, default_val={})
    return list(users.keys())

def delete_user(username: str) -> tuple[bool, str]:
    if username.lower() == "logicaldatasolution@gmail.com":
        return False, "Cannot delete the Master Admin."
        
    users, sha = read_json_db(USERS_FILE, default_val={})
    if username in users:
        del users[username]
        write_json_db(USERS_FILE, users, sha)
        return True, f"User {username} deleted."
    return False, "User not found."
