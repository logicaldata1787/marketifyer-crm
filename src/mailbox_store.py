import json
import os
from typing import List, Dict
import sys
from psycopg2.extras import RealDictCursor

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from config import get_db_connection
except ImportError:
    get_db_connection = None

MAILBOX_FILE = "mailboxes.json"

def load_mailboxes(username: str) -> List[Dict]:
    if get_db_connection:
        try:
            conn = get_db_connection()
            if conn:
                cur = conn.cursor(cursor_factory=RealDictCursor)
                cur.execute("SELECT * FROM mailboxes WHERE owner_username = %s", (username,))
                rows = cur.fetchall()
                cur.close()
                conn.close()
                
                mbs = []
                for row in rows:
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
    if get_db_connection:
        try:
            conn = get_db_connection()
            if conn:
                cur = conn.cursor(cursor_factory=RealDictCursor)
                cur.execute("SELECT * FROM mailboxes WHERE owner_username = %s AND smtp_user = %s AND host = %s", (username, user, host))
                row = cur.fetchone()
                if row:
                    cur.execute("UPDATE mailboxes SET smtp_password = %s, port = %s WHERE id = %s", (password, int(port), row['id']))
                else:
                    cur.execute("INSERT INTO mailboxes (owner_username, host, port, smtp_user, smtp_password) VALUES (%s, %s, %s, %s, %s)", (username, host, int(port), user, password))
                cur.close()
                conn.close()
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
    if get_db_connection:
        try:
            conn = get_db_connection()
            if conn:
                cur = conn.cursor()
                cur.execute("DELETE FROM mailboxes WHERE owner_username = %s AND smtp_user = %s AND host = %s", (username, user, host))
                cur.close()
                conn.close()
            return
        except: pass

    if not os.path.exists(MAILBOX_FILE): return
    with open(MAILBOX_FILE, 'r') as f:
        all_mbs = json.load(f)
        
    all_mbs = [mb for mb in all_mbs if not (mb.get('owner') == username and mb.get('user') == user and mb.get('host') == host)]
    
    with open(MAILBOX_FILE, 'w') as f:
        json.dump(all_mbs, f, indent=4)
