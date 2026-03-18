import json
import os
from typing import List, Dict

MAILBOX_FILE = "mailboxes.json"

def load_mailboxes(username: str) -> List[Dict]:
    """Load saved mailboxes owned by specific user from JSON storage."""
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
    if not os.path.exists(MAILBOX_FILE): return
    with open(MAILBOX_FILE, 'r') as f:
        all_mbs = json.load(f)
        
    all_mbs = [mb for mb in all_mbs if not (mb.get('owner') == username and mb.get('user') == user and mb.get('host') == host)]
    
    with open(MAILBOX_FILE, 'w') as f:
        json.dump(all_mbs, f, indent=4)
