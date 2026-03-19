import json
import os
import hashlib
from typing import Optional
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from config import supabase_client
except ImportError:
    supabase_client = None

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
    
    if supabase_client:
        try:
            res = supabase_client.table("users").select("*").eq("username", username).execute()
            if len(res.data) > 0:
                return False, "Username already exists."
            
            supabase_client.table("users").insert({
                "username": username,
                "password_hash": pw_hash
            }).execute()
            return True, "Cloud user created securely."
        except Exception as e:
            return False, f"Supabase Error: {e}"
            
    # Fallback to local JSON
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
    
    if supabase_client:
        try:
            res = supabase_client.table("users").select("*").eq("username", username).execute()
            if len(res.data) > 0:
                return res.data[0]["password_hash"] == pw_hash
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
    if supabase_client:
        try:
            res = supabase_client.table("users").select("id", count="exact").execute()
            return res.count > 0
        except: return False

    if not os.path.exists(USERS_FILE): return False
    with open(USERS_FILE, 'r') as f:
        users = json.load(f)
    return len(users) > 0

def get_all_users() -> list:
    if supabase_client:
        try:
            res = supabase_client.table("users").select("username").execute()
            return [row["username"] for row in res.data]
        except: return []

    if not os.path.exists(USERS_FILE): return []
    with open(USERS_FILE, 'r') as f:
        users = json.load(f)
    return list(users.keys())

def delete_user(username: str) -> tuple[bool, str]:
    if username.lower() == "logicaldatasolution@gmail.com":
        return False, "Cannot delete the Master Admin."
        
    if supabase_client:
        try:
            supabase_client.table("users").delete().eq("username", username).execute()
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
