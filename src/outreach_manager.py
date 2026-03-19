import smtplib
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import random
import pandas as pd
from typing import List, Dict
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config

class OutreachManager:
    def __init__(self, host=None, port=None, user=None, password=None):
        self.host = host or Config.SMTP_HOST
        self.port = int(port) if port is not None else Config.SMTP_PORT
        self.user = user or Config.SMTP_USER
        self.password = password or Config.SMTP_PASSWORD
        
    def test_connection(self) -> tuple[bool, str]:
        """Test SMTP connection with the current credentials."""
        if not self.user or not self.password or not self.host:
            return False, "Missing credentials or host."
            
        try:
            if self.port == 465:
                server = smtplib.SMTP_SSL(self.host, self.port, timeout=10)
            else:
                server = smtplib.SMTP(self.host, self.port, timeout=10)
                server.starttls()
            
            server.login(self.user, self.password)
            server.quit()
            return True, "Success"
        except Exception as e:
            print(f"SMTP Test Error: {e}")
            return False, str(e)
        
    def _create_message(self, to_email: str, subject: str, html_content: str, reply_to: str = "") -> MIMEMultipart:
        msg = MIMEMultipart()
        msg['From'] = self.user
        msg['To'] = to_email
        msg['Subject'] = subject
        if reply_to and reply_to.strip():
            msg.add_header('reply-to', reply_to.strip())
        msg.attach(MIMEText(html_content, 'html'))
        return msg

    def send_campaign(self, contacts_df: pd.DataFrame, subject_template: str, body_template: str, subject_b: str = None, body_b: str = None, reply_to: str = "", min_delay: int = 60, max_delay: int = 300, campaign_id: str = None, include_unsubscribe: bool = True, progress_callback=None) -> Dict[str, int]:
        """
        Sends emails one by one with a random delay (between min_delay and max_delay in seconds)
        to simulate human sending behavior.
        Returns: Dict containing basic stats (sent, failed, total).
        """
        stats = {"sent": 0, "failed": 0, "total": 0}
        
        # Filter contacts with empty or invalid emails first
        valid_df = contacts_df.dropna(subset=['Email'])
        valid_df = valid_df[valid_df['Email'] != ""]
        stats["total"] = len(valid_df)
        
        if stats["total"] == 0:
            if progress_callback:
                progress_callback(stats, "No valid emails found in the list.")
            return stats
            
        if not self.user or not self.password:
            print("Error: SMTP credentials not provided.")
            stats["failed"] = stats["total"]
            if progress_callback:
                progress_callback(stats, "SMTP credentials missing.")
            return stats

        server = None
        try:
            print(f"Connecting to SMTP server {self.host}:{self.port}...")
            if progress_callback:
                progress_callback(stats, f"Connecting to SMTP server...")
                
            if self.port == 465:
                server = smtplib.SMTP_SSL(self.host, self.port)
            else:
                server = smtplib.SMTP(self.host, self.port)
                server.starttls()
            
            server.login(self.user, self.password)
            print("SMTP Login successful.")
            
            for index, row in valid_df.iterrows():
                email = row.get('Email')
                name = row.get('Name', 'there')
                company = row.get('Company', 'your company')
                
                if subject_b and body_b and index % 2 != 0:
                    current_subject_template = subject_b
                    current_body_template = body_b
                else:
                    current_subject_template = subject_template
                    current_body_template = body_template
                
                subject = current_subject_template.replace("{{name}}", str(name)).replace("{{company}}", str(company))
                body = current_body_template.replace("{{name}}", str(name)).replace("{{company}}", str(company))
                
                # Format literal text linebreaks into HTML breaks so emails do not render as a single generic string
                body = body.replace("\n", "<br>")
                
                # INJECT TRUE OPEN TRACKING PIXEL IF LIVE CONFIG
                if campaign_id:
                    pixel_url = f"https://marketifyer.streamlit.app/?action=open&cid={campaign_id}"
                    pixel_html = f'<img src="{pixel_url}" width="1" height="1" alt="" style="display:none;" />'
                    if "</body>" in body.lower():
                        body = re.sub(r'</body>', f'{pixel_html}</body>', body, flags=re.IGNORECASE)
                    else:
                        body += pixel_html
                        
                # INJECT UNSUBSCRIBE LINK
                if include_unsubscribe:
                    unsub_url = f"https://marketifyer.streamlit.app/?action=unsub&email={email}"
                    unsub_html = f'<br><br><p style="font-size: 11px; color: #888;">If you wish to opt out of future communications, please <a href="{unsub_url}">unsubscribe here</a>.</p>'
                    if "</body>" in body.lower():
                        body = re.sub(r'</body>', f'{unsub_html}</body>', body, flags=re.IGNORECASE)
                    else:
                        body += unsub_html
                
                msg = self._create_message(email, subject, body, reply_to)
                
                print(f"Sending email to {email} ({name} at {company})...")
                if progress_callback:
                    progress_callback(stats, f"Sending email to {email}...")
                    
                try:
                    server.send_message(msg)
                    print(f"Sent successfully to {email}.")
                    stats["sent"] += 1
                except Exception as loop_e:
                    print(f"Failed to send to {email}: {loop_e}")
                    stats["failed"] += 1
                    if progress_callback:
                        progress_callback(stats, f"Failed: {email}")
                    continue
                
                if progress_callback:
                    progress_callback(stats, f"Sent successfully to {email}.")
                
                # Check if it's the last email to avoid unnecessary delay at the end
                if index < len(valid_df) - 1:
                    delay = random.randint(min_delay, max_delay)
                    print(f"Waiting for {delay} seconds before next email to mimic human pacing...")
                    if progress_callback:
                        progress_callback(stats, f"Waiting {delay}s before next email...")
                    time.sleep(delay)
                    
            # Compute simulated metrics based on Sent count for tracking visibility
            if stats['sent'] > 0:
                stats['simulated_opened'] = int(stats['sent'] * random.uniform(0.35, 0.65))
                stats['simulated_replied'] = int(stats['simulated_opened'] * random.uniform(0.05, 0.25))
            else:
                stats['simulated_opened'] = 0
                stats['simulated_replied'] = 0
                    
        except Exception as e:
            print(f"Critical campaign failure: {e}")
            stats["failed"] += (stats["total"] - stats["sent"] - stats["failed"])
            if progress_callback:
                progress_callback(stats, f"Critical Failure: {e}")
        finally:
            if server:
                try:
                    server.quit()
                    print("SMTP connection closed.")
                except:
                    pass
        return stats
