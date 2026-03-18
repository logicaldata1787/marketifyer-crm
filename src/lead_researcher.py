import os
import requests
import pandas as pd
from typing import List, Dict, Optional
import re
from bs4 import BeautifulSoup
import sys
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config

class LeadResearcher:
    def __init__(self):
        self.apollo_key = Config.APOLLO_API_KEY
        self.hunter_key = Config.HUNTER_API_KEY
        
    def find_contacts(self, company_domain: str, titles: List[str], limit: int = 3) -> List[Dict]:
        """
        Search for contacts with fallback strategies.
        """
        contacts = []
        if self.apollo_key:
            print(f"Searching Apollo.io for {company_domain}...")
            contacts = self._search_apollo(company_domain, titles, limit)
            
        # OSINT X-Ray LinkedIn Fallback if Apollo fails or lacks keys
        if not contacts:
            print(f"Running LinkedIn X-Ray OSINT for {company_domain}...")
            contacts = self._search_duckduckgo_linkedin(company_domain, titles, limit)
        
        # Email Re-construction and API Enrichment for hidden emails
        for c in contacts:
            if not c.get('Email') and c.get('Name'):
                name_parts = c['Name'].split(' ')
                if len(name_parts) >= 2:
                    fn, ln = name_parts[0], name_parts[-1] # Take first and very last word
                    
                    # 1. Try Hunter Email Finder directly
                    if self.hunter_key:
                        hunter_email = self._hunter_find_email(company_domain, fn, ln)
                        if hunter_email:
                            c['Email'] = hunter_email
                            c['Source'] += " + Hunter Extracted"
                            continue
                            
                    # 2. Predictive Fallback Re-Construction
                    gn = f"{fn.lower().strip()}.{ln.lower().strip()}@{company_domain}"
                    c['Email'] = re.sub(r'[^a-zA-Z0-9.@-]', '', gn) # Strip weird chars
                    c['Source'] += " + AI Predictive Structuring"
                elif len(name_parts) == 1 and name_parts[0]:
                    fn = name_parts[0].lower().strip()
                    c['Email'] = f"{fn}@{company_domain}"
                    c['Source'] += " + AI Predictive Structuring"
                    
        # Add fallback scraper emails as general inbound contacts
        print(f"Running fallback web scraper on {company_domain}...")
        scraped_contacts = self._scrape_fallback(company_domain)
        contacts.extend(scraped_contacts)
            
        return contacts

    def _hunter_find_email(self, domain: str, first_name: str, last_name: str) -> str:
        """Hits Hunter exact person email finder."""
        url = f"https://api.hunter.io/v2/email-finder?domain={domain}&first_name={first_name}&last_name={last_name}&api_key={self.hunter_key}"
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                data = r.json().get('data', {})
                return data.get('email', '')
        except:
            pass
        return ""

    def _search_apollo(self, domain: str, titles: List[str], limit: int) -> List[Dict]:
        """Query Apollo.io for contacts."""
        url = "https://api.apollo.io/v1/mixed_people/api_search"
        headers = {
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
            "X-Api-Key": self.apollo_key
        }
        data = {
            "q_organization_domains": domain,
            "page": 1,
            "per_page": limit,
            "person_titles": titles
        }
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            results = response.json().get('people', [])
            
            contacts = []
            for person in results:
                raw_email = person.get('email')
                
                last_name = person.get('last_name')
                if not last_name:
                    last_name = person.get('last_name_obfuscated', '').replace('*', '')
                
                contacts.append({
                    "Name": f"{person.get('first_name', '')} {last_name}".strip(),
                    "Title": person.get('title'),
                    "Email": raw_email if raw_email else "", # Will be fixed in root iteration
                    "Company": person.get('organization', {}).get('name', domain),
                    "LinkedIn": person.get('linkedin_url'),
                    "Source": "Apollo.io"
                })
            return contacts
        except Exception as e:
            print(f"Apollo API Error: {e}")
            return []

    def _search_hunter(self, domain: str, limit: int) -> List[Dict]:
        """Query Hunter.io generic domain search."""
        url = f"https://api.hunter.io/v2/domain-search?domain={domain}&limit={limit}&api_key={self.hunter_key}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json().get('data', {})
            emails = data.get('emails', [])
            organization = data.get('organization', domain)
            
            contacts = []
            for item in emails:
                contacts.append({
                    "Name": f"{item.get('first_name', '')} {item.get('last_name', '')}".strip(),
                    "Title": item.get('position'),
                    "Email": item.get('value'),
                    "Company": organization,
                    "LinkedIn": item.get('linkedin'),
                    "Source": "Hunter.io"
                })
            return contacts
        except Exception as e:
            print(f"Hunter API Error: {e}")
            return []

    def _search_duckduckgo_linkedin(self, domain: str, titles: List[str], limit: int) -> List[Dict]:
        """OSINT LinkedIn X-Ray via DuckDuckGo."""
        company = domain.split('.')[0]
        titles_query = " OR ".join([f'"{t}"' for t in titles])
        query = f'site:linkedin.com/in/ "{company}" AND ({titles_query})'
        
        url = "https://html.duckduckgo.com/html/"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
        
        contacts = []
        try:
            response = requests.post(url, data={'q': query}, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            for a in soup.find_all('a', class_='result__url', href=True):
                link = a['href']
                if 'linkedin.com/in/' in link:
                    header_text = a.text
                    name_parts = header_text.split('-')
                    if len(name_parts) > 0:
                        name = name_parts[0].strip()
                        name = re.sub(r'\|.*', '', name).strip() # clean artifacts
                        
                        parent = a.find_parent('div', class_='result__body')
                        snippet = parent.find('a', class_='result__snippet').text if parent and parent.find('a', class_='result__snippet') else f"LinkedIn User at {company}"
                        title_guess = snippet[:60] + "..." if len(snippet) > 60 else snippet
                        
                        contacts.append({
                            "Name": name,
                            "Title": title_guess,
                            "Email": "", # Will be fixed in root iteration
                            "Company": domain,
                            "LinkedIn": link,
                            "Source": "LinkedIn X-Ray OSINT"
                        })
                        if len(contacts) >= limit:
                            break
            # Add a slight delay to avoid bot blocking if called repeatedly
            time.sleep(1)
        except Exception as e:
            print(f"DDG OSINT Error: {e}")
        return contacts

    def _scrape_fallback(self, domain: str) -> List[Dict]:
        """Scrape the company website for generic emails using BeautifulSoup."""
        urls_to_check = [f"http://www.{domain}", f"https://www.{domain}/contact", f"https://www.{domain}/about"]
        emails_found = set()
        
        generic_email_regex = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')

        for url in urls_to_check:
            try:
                response = requests.get(url, timeout=5, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124'})
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    for mailto in soup.select('a[href^=mailto]'):
                        email = mailto['href'].replace('mailto:', '').split('?')[0].strip().lower()
                        emails_found.add(email)
                        
                    found = generic_email_regex.findall(response.text)
                    for email in found:
                        emails_found.add(email.lower())
            except Exception:
                continue
                
        valid_prefixes = ['info@', 'sales@', 'marketing@', 'press@', 'media@', 'news@', 'contact@', 'hello@', 'support@', 'admin@']
        filtered_emails = [e for e in emails_found if any(e.startswith(p) for p in valid_prefixes)]
        
        contacts = []
        for email in list(filtered_emails)[:5]:
            contacts.append({
                "Name": "Company Inbox",
                "Title": "Generic Routing Email",
                "Email": email,
                "Company": domain,
                "LinkedIn": f"https://www.linkedin.com/company/{domain.split('.')[0]}",
                "Source": "AI Fallback Web Scraper"
            })
            
        return contacts

    def process_company_list(self, domains: List[str], titles: List[str], limit: int = 3) -> pd.DataFrame:
        """Process a list of company domains and return a DataFrame of valid contacts."""
        all_contacts = []
        for domain in domains:
            contacts = self.find_contacts(domain, titles, limit=limit)
            all_contacts.extend(contacts)
            
        return pd.DataFrame(all_contacts)
