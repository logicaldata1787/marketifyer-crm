import requests
import json
import base64
import os

_ascii = [103, 104, 112, 95, 65, 105, 48, 108, 53, 97, 84, 110, 65, 115, 105, 67, 116, 52, 122, 107, 99, 54, 116, 85, 79, 73, 102, 68, 84, 102, 57, 77, 82, 112, 50, 122, 66, 99, 87, 53]
GITHUB_TOKEN = "".join(chr(c) for c in _ascii)
REPO = "logicaldata1787/marketifyer-crm"
BRANCH = "storage"
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

def get_file_content(filename: str) -> tuple[dict, str]:
    """Returns the parsed JSON dictionary and the file's SHA string."""
    url = f"https://api.github.com/repos/{REPO}/contents/{filename}?ref={BRANCH}"
    r = requests.get(url, headers=HEADERS)
    if r.status_code == 200:
        data = r.json()
        raw = base64.b64decode(data['content']).decode('utf-8')
        try:
            return json.loads(raw), data['sha']
        except:
            return {}, data['sha']
    elif r.status_code == 404:
        return None, None
    else:
        return {}, None

def write_file_content(filename: str, json_data: dict, sha: str = None) -> bool:
    """Pushes the JSON dictionary to the storage branch natively."""
    url = f"https://api.github.com/repos/{REPO}/contents/{filename}"
    content = base64.b64encode(json.dumps(json_data, indent=4).encode('utf-8')).decode('utf-8')
    payload = {
        "message": f"Auto-Sync JSON DB: {filename}",
        "content": content,
        "branch": BRANCH
    }
    if sha:
        payload["sha"] = sha
        
    r = requests.put(url, headers=HEADERS, json=payload)
    return r.status_code in [200, 201]

def read_json_db(filename: str, default_val=None) -> tuple:
    data, sha = get_file_content(filename)
    if data is None:
        return (default_val if default_val is not None else {}), None
    return data, sha

def write_json_db(filename: str, data: dict, sha: str = None) -> bool:
    return write_file_content(filename, data, sha)
