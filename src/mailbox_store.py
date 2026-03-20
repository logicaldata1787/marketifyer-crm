from typing import List, Dict
import sys
import os
import base64

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.github_storage import read_json_db, write_json_db, GITHUB_TOKEN

MAILBOX_FILE = "mailboxes.json"

def _xor_crypt(data: str, key: str) -> str:
    res = []
    for i in range(len(data)):
        res.append(chr(ord(data[i]) ^ ord(key[i % len(key)])))
    return "".join(res)

def encode_pwd(pwd: str) -> str:
    xored = _xor_crypt(pwd, GITHUB_TOKEN)
    return "XOR_" + base64.b64encode(xored.encode('utf-8')).decode('utf-8')

def decode_pwd(enc: str) -> str:
    if not isinstance(enc, str): return enc
    if enc.startswith("XOR_"):
        try:
            xored = base64.b64decode(enc[4:].encode('utf-8')).decode('utf-8')
            return _xor_crypt(xored, GITHUB_TOKEN)
        except: return enc
    return enc

def load_mailboxes(username: str) -> List[Dict]:
    mbs, _ = read_json_db(MAILBOX_FILE, default_val=[])
    ret = []
    for mb in mbs:
        if mb.get('owner') == username:
            n_mb = mb.copy()
            n_mb['password'] = decode_pwd(mb.get('password', ''))
            ret.append(n_mb)
    return ret

def save_mailbox(username: str, host: str, port: str, user: str, password: str):
    all_mbs, sha = read_json_db(MAILBOX_FILE, default_val=[])
            
    updated = False
    enc_pwd = encode_pwd(password)
    
    for mb in all_mbs:
        if mb.get('owner') == username and mb.get('user') == user and mb.get('host') == host:
            mb['password'] = enc_pwd
            mb['port'] = port
            updated = True
            break
            
    if not updated:
        all_mbs.append({
            "owner": username,
            "host": host,
            "port": port,
            "user": user,
            "password": enc_pwd
        })
        
    write_json_db(MAILBOX_FILE, all_mbs, sha)
        
def delete_mailbox(username: str, user: str, host: str):
    all_mbs, sha = read_json_db(MAILBOX_FILE, default_val=[])
    new_mbs = [mb for mb in all_mbs if not (mb.get('owner') == username and mb.get('user') == user and mb.get('host') == host)]
    if len(new_mbs) < len(all_mbs):
        write_json_db(MAILBOX_FILE, new_mbs, sha)
