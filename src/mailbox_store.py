import json
import os
from typing import List, Dict
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from config import supabase_client
except ImportError:
    supabase_client = None

MAILBOX_FILE = "mailboxes.json"

def load_mailboxes(username: str) -> List[Dict]:
    """Load saved mailboxes owned by specific user from JSON or Supabase."""
    if supabase_client:
        try:
            res = supabase_client.table("mailboxes").select("*").eq("owner_username", username).execute()
            mbs = []
            for row in res.data:
                mbs.append({
                    "owner": row["owner_username"],
                    "host": row["host"],
                    "port": str(row["port"]),
                    "user": row["smtp_user"],
                    "password": row["smtp_password"]
                })
            return mbs
        except Exception:
            pass

    if not os.path.exists(MAILBOX_FILE):
        return []
    try:
        with open(MAILBOX_FILE, 'r') as f:
            all_mbs = json.load(f)
            return [mb for mb in all_mbs if mb.get('owner') == username]
    except Exception:
        return []

def save_mailbox(username: str, host: str, port: str, user: str, password: str):
    """Save a successfully tested mailbox specifically linking it to an owner."""
    if supabase_client:
        try:
            res = supabase_client.table("mailboxes").select("*").eq("owner_username", username).eq("smtp_user", user).eq("host", host).execute()
            if len(res.data) > 0:
                supabase_client.table("mailboxes").update({
                    "smtp_password": password,
                    "port": int(port)
                }).eq("id", res.data[0]["id"]).execute()
            else:
                supabase_client.table("mailboxes").insert({
                    "owner_username": username,
                    "host": host,
                    "port": int(port),
                    "smtp_user": user,
                    "smtp_password": password
                }).execute()
            return
        except Exception:
            pass

    all_mbs = []
    if os.path.exists(MAILBOX_FILE):
        try:
            with open(MAILBOX_FILE, 'r') as f:
                all_mbs = json.load(f)
        except Exception:
            pass
            
    updated = False
    for mb in all_mbs:
        if mb.get('owner') == username and mb.get('user') == user and mb.get('host') == host:
            mb['password'] = password
            mb['port'] = port
            updated = True
            break
            
    if not updated:
        all_mbs.append({
            "owner": username,
            "host": host,
            "port": port,
            "user": user,
            "password": password
        })
        
    with open(MAILBOX_FILE, 'w') as f:
        json.dump(all_mbs, f, indent=4)
        
def delete_mailbox(username: str, user: str, host: str):
    """Delete a mailbox owned by user from persistent storage."""
    if supabase_client:
        try:
            supabase_client.table("mailboxes").delete().eq("owner_username", username).eq("smtp_user", user).eq("host", host).execute()
            return
        except: pass

    if not os.path.exists(MAILBOX_FILE): return
    with open(MAILBOX_FILE, 'r') as f:
        all_mbs = json.load(f)
        
    all_mbs = [mb for mb in all_mbs if not (mb.get('owner') == username and mb.get('user') == user and mb.get('host') == host)]
    
    with open(MAILBOX_FILE, 'w') as f:
        json.dump(all_mbs, f, indent=4)
