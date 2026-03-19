import json
import os
from datetime import datetime
from typing import List, Dict
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from config import supabase_client
except ImportError:
    supabase_client = None

CAMPAIGNS_FILE = "campaigns.json"

def load_all_campaigns_admin() -> List[Dict]:
    if supabase_client:
        try:
            res = supabase_client.table("campaigns").select("*").execute()
            camps = []
            for row in res.data:
                camps.append({
                    "id": str(row["id"]),
                    "owner": row["owner_username"],
                    "date": row["date"],
                    "name": row["name"],
                    "subject": row["subject"],
                    "list_size": row["total_leads"],
                    "sent": row["sent"],
                    "failed": row["failed"],
                    "delivered": row["sent"],
                    "opened": row["opened"],
                    "replied": row["replied"]
                })
            return camps
        except: pass

    if not os.path.exists(CAMPAIGNS_FILE): return []
    try:
        with open(CAMPAIGNS_FILE, 'r') as f:
            return json.load(f)
    except Exception: return []

def load_campaigns(username: str) -> List[Dict]:
    if supabase_client:
        try:
            res = supabase_client.table("campaigns").select("*").eq("owner_username", username).execute()
            camps = []
            for row in res.data:
                camps.append({
                    "id": str(row["id"]),
                    "owner": row["owner_username"],
                    "date": row["date"],
                    "name": row["name"],
                    "subject": row["subject"],
                    "list_size": row["total_leads"],
                    "sent": row["sent"],
                    "failed": row["failed"],
                    "delivered": row["sent"],
                    "opened": row["opened"],
                    "replied": row["replied"]
                })
            return camps
        except: pass

    if not os.path.exists(CAMPAIGNS_FILE): return []
    try:
        with open(CAMPAIGNS_FILE, 'r') as f:
            all_camps = json.load(f)
            return [c for c in all_camps if c.get('owner') == username]
    except Exception: return []

def save_campaign(campaign_id: str, username: str, campaign_name: str, subject: str, list_size: int, sent: int, failed: int, simulated_opened: int, simulated_replied: int):
    c_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if supabase_client:
        try:
            supabase_client.table("campaigns").insert({
                "id": campaign_id,
                "owner_username": username,
                "name": campaign_name,
                "subject": subject,
                "date": c_date,
                "total_leads": list_size,
                "sent": sent,
                "failed": failed,
                "opened": simulated_opened,
                "replied": simulated_replied
            }).execute()
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
    if supabase_client:
        try:
            if len(str(campaign_id)) > 20: 
                supabase_client.table("campaigns").delete().eq("id", campaign_id).execute()
                return
        except: pass

    if not os.path.exists(CAMPAIGNS_FILE): return
    with open(CAMPAIGNS_FILE, 'r') as f:
        all_camps = json.load(f)
    all_camps = [c for c in all_camps if not (c.get('owner') == username and c.get('id') == campaign_id)]
    with open(CAMPAIGNS_FILE, 'w') as f:
        json.dump(all_camps, f, indent=4)
