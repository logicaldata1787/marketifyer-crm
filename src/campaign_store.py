import json
import os
from datetime import datetime
from typing import List, Dict
import sys
from psycopg2.extras import RealDictCursor

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from config import get_db_connection
except ImportError:
    get_db_connection = None

CAMPAIGNS_FILE = "campaigns.json"

def _format_rows(rows) -> List[Dict]:
    camps = []
    for row in rows:
        raw_s = row["subject"]
        c_subj = raw_s.split("||||")[0] if "||||" in raw_s else raw_s
        c_body = raw_s.split("||||")[1] if "||||" in raw_s else "Copy tracking uninitialized"
        camps.append({
            "id": str(row["id"]),
            "owner": row["owner_username"],
            "date": row["date"].strftime("%Y-%m-%d %H:%M:%S") if isinstance(row["date"], datetime) else str(row["date"]),
            "name": row["name"],
            "subject": c_subj,
            "body": c_body,
            "list_size": row["total_leads"],
            "sent": row["sent"],
            "failed": row["failed"],
            "delivered": row["sent"],
            "opened": row["opened"],
            "replied": row["replied"]
        })
    return camps

def load_all_campaigns_admin() -> List[Dict]:
    if get_db_connection:
        try:
            conn = get_db_connection()
            if conn:
                cur = conn.cursor(cursor_factory=RealDictCursor)
                cur.execute("SELECT * FROM campaigns ORDER BY date ASC")
                rows = cur.fetchall()
                cur.close()
                conn.close()
                return _format_rows(rows)
        except: pass

    if not os.path.exists(CAMPAIGNS_FILE): return []
    try:
        with open(CAMPAIGNS_FILE, 'r') as f:
            return json.load(f)
    except Exception: return []

def load_campaigns(username: str) -> List[Dict]:
    if get_db_connection:
        try:
            conn = get_db_connection()
            if conn:
                cur = conn.cursor(cursor_factory=RealDictCursor)
                cur.execute("SELECT * FROM campaigns WHERE owner_username = %s ORDER BY date ASC", (username,))
                rows = cur.fetchall()
                cur.close()
                conn.close()
                return _format_rows(rows)
        except: pass

    if not os.path.exists(CAMPAIGNS_FILE): return []
    try:
        with open(CAMPAIGNS_FILE, 'r') as f:
            all_camps = json.load(f)
            return [c for c in all_camps if c.get('owner') == username]
    except Exception: return []

def save_campaign(campaign_id: str, username: str, campaign_name: str, subject: str, body: str, list_size: int, sent: int, failed: int, simulated_opened: int, simulated_replied: int):
    c_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db_subj = f"{subject}||||{body}"
    
    if get_db_connection:
        try:
            conn = get_db_connection()
            if conn:
                cur = conn.cursor()
                cur.execute("INSERT INTO campaigns (id, owner_username, name, subject, date, total_leads, sent, failed, opened, replied) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (campaign_id, username, campaign_name, db_subj, c_date, list_size, sent, failed, simulated_opened, simulated_replied))
                cur.close()
                conn.close()
            return
        except Exception: pass

    all_camps = []
    if os.path.exists(CAMPAIGNS_FILE):
        try:
            with open(CAMPAIGNS_FILE, 'r') as f:
                all_camps = json.load(f)
        except Exception: pass
            
    new_campaign = {
        "id": campaign_id,
        "owner": username,
        "date": c_date,
        "name": campaign_name,
        "subject": subject,
        "body": body,
        "list_size": list_size,
        "sent": sent,
        "failed": failed,
        "delivered": sent,
        "opened": simulated_opened,
        "replied": simulated_replied
    }
    all_camps.append(new_campaign)
    with open(CAMPAIGNS_FILE, 'w') as f:
        json.dump(all_camps, f, indent=4)

def delete_campaign(username: str, campaign_id: str):
    if get_db_connection:
        try:
            if len(str(campaign_id)) > 20: 
                conn = get_db_connection()
                if conn:
                    cur = conn.cursor()
                    cur.execute("DELETE FROM campaigns WHERE id = %s", (campaign_id,))
                    cur.close()
                    conn.close()
                return
        except: pass

    if not os.path.exists(CAMPAIGNS_FILE): return
    with open(CAMPAIGNS_FILE, 'r') as f:
        all_camps = json.load(f)
    all_camps = [c for c in all_camps if not (c.get('owner') == username and c.get('id') == campaign_id)]
    with open(CAMPAIGNS_FILE, 'w') as f:
        json.dump(all_camps, f, indent=4)
