from typing import List, Dict
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.github_storage import read_json_db, write_json_db

MAILBOX_FILE = "mailboxes.json"

def load_mailboxes(username: str) -> List[Dict]:
    mbs, _ = read_json_db(MAILBOX_FILE, default_val=[])
    return [mb for mb in mbs if mb.get('owner') == username]

def save_mailbox(username: str, host: str, port: str, user: str, password: str):
    all_mbs, sha = read_json_db(MAILBOX_FILE, default_val=[])
            
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
        
    write_json_db(MAILBOX_FILE, all_mbs, sha)
        
def delete_mailbox(username: str, user: str, host: str):
    all_mbs, sha = read_json_db(MAILBOX_FILE, default_val=[])
    new_mbs = [mb for mb in all_mbs if not (mb.get('owner') == username and mb.get('user') == user and mb.get('host') == host)]
    if len(new_mbs) < len(all_mbs):
        write_json_db(MAILBOX_FILE, new_mbs, sha)
