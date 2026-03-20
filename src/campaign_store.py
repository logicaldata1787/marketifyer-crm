from datetime import datetime
from typing import List, Dict
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.github_storage import read_json_db, write_json_db

CAMPAIGNS_FILE = "campaigns.json"

def load_all_campaigns_admin() -> List[Dict]:
    all_camps, _ = read_json_db(CAMPAIGNS_FILE, default_val=[])
    return all_camps

def load_campaigns(username: str) -> List[Dict]:
    all_camps, _ = read_json_db(CAMPAIGNS_FILE, default_val=[])
    return [c for c in all_camps if c.get('owner') == username]

def save_campaign(campaign_id: str, username: str, campaign_name: str, subject: str, body: str, list_size: int, sent: int, failed: int, simulated_opened: int, simulated_replied: int):
    c_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    all_camps, sha = read_json_db(CAMPAIGNS_FILE, default_val=[])
            
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
    write_json_db(CAMPAIGNS_FILE, all_camps, sha)

def delete_campaign(username: str, campaign_id: str):
    all_camps, sha = read_json_db(CAMPAIGNS_FILE, default_val=[])
    new_camps = [c for c in all_camps if not (c.get('owner') == username and c.get('id') == campaign_id)]
    if len(new_camps) < len(all_camps):
        write_json_db(CAMPAIGNS_FILE, new_camps, sha)
