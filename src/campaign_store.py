import json
import os
from datetime import datetime
from typing import List, Dict

CAMPAIGNS_FILE = "campaigns.json"

def load_all_campaigns_admin() -> List[Dict]:
    if not os.path.exists(CAMPAIGNS_FILE):
        return []
    try:
        with open(CAMPAIGNS_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return []

def load_campaigns(username: str) -> List[Dict]:
    if not os.path.exists(CAMPAIGNS_FILE):
        return []
    try:
        with open(CAMPAIGNS_FILE, 'r') as f:
            all_camps = json.load(f)
            return [c for c in all_camps if c.get('owner') == username]
    except Exception:
        return []

def save_campaign(username: str, campaign_name: str, subject: str, list_size: int, sent: int, failed: int, simulated_opened: int, simulated_replied: int):
    all_camps = []
    if os.path.exists(CAMPAIGNS_FILE):
        try:
            with open(CAMPAIGNS_FILE, 'r') as f:
                all_camps = json.load(f)
        except Exception:
            pass
            
    new_campaign = {
        "id": datetime.now().strftime("%Y%m%d%H%M%S"),
        "owner": username,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "name": campaign_name,
        "subject": subject,
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
    if not os.path.exists(CAMPAIGNS_FILE): return
    with open(CAMPAIGNS_FILE, 'r') as f:
        all_camps = json.load(f)
    all_camps = [c for c in all_camps if not (c.get('owner') == username and c.get('id') == campaign_id)]
    with open(CAMPAIGNS_FILE, 'w') as f:
        json.dump(all_camps, f, indent=4)
