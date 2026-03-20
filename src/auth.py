import json
import os
import hashlib
from typing import Optional
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from config import get_db_connection
except ImportError:
    get_db_connection = None

USERS_FILE = "users.json"

def _hash_pw(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def init_users_db() -> bool:
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w') as f:
            json.dump({}, f)
        return False
    return True

def create_user(username: str, password: str) -> tuple[bool, str]:
    pw_hash = _hash_pw(password)
    
    if get_db_connection:
        try:
            conn = get_db_connection()
            if conn:
                cur = conn.cursor()
                cur.execute("SELECT * FROM users WHERE username = %s", (username,))
                if cur.fetchone():
                    conn.close()
                    return False, "Username already exists."
                
                cur.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)", (username, pw_hash))
                cur.close()
                conn.close()
                return True, "Cloud user created securely."
        except Exception as e:
            return False, f"Supabase Error: {e}"
            
    # Fallback
    init_users_db()
    with open(USERS_FILE, 'r') as f:
        users = json.load(f)
        
    if username in users:
        return False, "Username already exists."
        
    users[username] = {"password_hash": pw_hash}
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)
    return True, "User created successfully."

def authenticate(username: str, password: str) -> bool:
    pw_hash = _hash_pw(password)
    
    if get_db_connection:
        try:
            conn = get_db_connection()
            if conn:
                cur = conn.cursor()
                cur.execute("SELECT password_hash FROM users WHERE username = %s", (username,))
                row = cur.fetchone()
                cur.close()
                conn.close()
                if row:
                    return row[0] == pw_hash
                return False
        except Exception:
            return False

    if not os.path.exists(USERS_FILE): return False
    with open(USERS_FILE, 'r') as f:
        users = json.load(f)
        
    if username in users and users[username]["password_hash"] == pw_hash:
        return True
    return False

def users_exist() -> bool:
    if get_db_connection:
        try:
            conn = get_db_connection()
            if conn:
                cur = conn.cursor()
                cur.execute("SELECT COUNT(id) FROM users")
                cnt = cur.fetchone()[0]
                cur.close()
                conn.close()
                return cnt > 0
        except: return False

    if not os.path.exists(USERS_FILE): return False
    with open(USERS_FILE, 'r') as f:
        users = json.load(f)
    return len(users) > 0

def get_all_users() -> list:
    if get_db_connection:
        try:
            conn = get_db_connection()
            if conn:
                cur = conn.cursor()
                cur.execute("SELECT username FROM users")
                rows = [r[0] for r in cur.fetchall()]
                cur.close()
                conn.close()
                return rows
        except: return []

    if not os.path.exists(USERS_FILE): return []
    with open(USERS_FILE, 'r') as f:
        users = json.load(f)
    return list(users.keys())

def delete_user(username: str) -> tuple[bool, str]:
    if username.lower() == "logicaldatasolution@gmail.com":
        return False, "Cannot delete the Master Admin."
        
    if get_db_connection:
        try:
            conn = get_db_connection()
            if conn:
                cur = conn.cursor()
                cur.execute("DELETE FROM users WHERE username = %s", (username,))
                cur.close()
                conn.close()
                return True, f"Cloud User {username} deleted."
        except Exception as e:
            return False, str(e)

    if not os.path.exists(USERS_FILE): return False, "Database missing."
    with open(USERS_FILE, 'r') as f:
        users = json.load(f)
        
    if username in users:
        del users[username]
        with open(USERS_FILE, 'w') as f:
            json.dump(users, f, indent=4)
        return True, f"User {username} deleted."
    return False, "User not found."
