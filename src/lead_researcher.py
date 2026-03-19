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
        
    def resolve_company_to_domain(self, company: str) -> str:
        """Use DuckDuckGo to find the domain of a company name."""
        url = "https://html.duckduckgo.com/html/"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        try:
            res = requests.post(url, data={'q': f'"{company}" official website'}, headers=headers, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            for a in soup.find_all('a', class_='result__url'):
                href = a.get('href', '')
                if 'wikipedia' not in href and 'linkedin' not in href and 'facebook' not in href and 'twitter' not in href:
                    domain_match = re.search(r'https?://(?:www\.)?([^/]+)', href)
                    if domain_match:
                        return domain_match.group(1).split('/')[0]
        except Exception:
            pass
        clean_name = re.sub(r'[^a-zA-Z0-9]', '', company).lower()
        return f"{clean_name}.com"

    def extract_event_exhibitors(self, event_name: str) -> List[str]:
        """Scrape DDG for an event's exhibitor list and extract company names/domains."""
        url = "https://html.duckduckgo.com/html/"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        companies = []
        try:
            res = requests.post(url, data={'q': f'"{event_name}" exhibitors sponsors list'}, headers=headers, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            for snippet in soup.find_all('a', class_='result__snippet'):
                text = snippet.text
                words = re.findall(r'\b[A-Z][a-zA-Z0-9_]+\b', text)
                for w in words:
                    if len(w) > 3 and w.lower() not in ['event', 'sponsor', 'exhibitor', 'booth', 'hall', 'the', 'and', 'inc', 'llc', 'company', 'solutions']:
                        if w not in companies:
                            companies.append(w)
            return list(set(companies))[:15]
        except:
            return []

    def _get_hunter_pattern(self, domain: str) -> str:
        """Get structural email pattern from Hunter."""
        if not self.hunter_key: return "{f}.{last}"
        url = f"https://api.hunter.io/v2/domain-search?domain={domain}&api_key={self.hunter_key}"
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                pattern = r.json().get('data', {}).get('pattern')
                if pattern: return pattern
        except: pass
        return "{first}.{last}"

    def build_email_permutations(self, first: str, last: str, domain: str, pattern: str) -> List[str]:
        """Build email guesses based on pattern and statistics."""
        f, l = first.lower().strip(), last.lower().strip()
        fi = f[0] if f else ""
        li = l[0] if l else ""
        
        emails = []
        if pattern:
            p = pattern.lower()
            if "{first}.{last}" in p: emails.append(f"{f}.{l}@{domain}")
            elif "{first}{last}" in p: emails.append(f"{f}{l}@{domain}")
            elif "{f}{last}" in p: emails.append(f"{fi}{l}@{domain}")
            elif "{first}{l}" in p: emails.append(f"{f}{li}@{domain}")
            elif "{first}" in p: emails.append(f"{f}@{domain}")
            elif "{last}" in p: emails.append(f"{l}@{domain}")
            
        fallbacks = [
            f"{f}.{l}@{domain}", f"{f}@{domain}", f"{fi}{l}@{domain}", f"{f}{l}@{domain}"
        ]
        for fb in fallbacks:
            clean_fb = re.sub(r'[^a-zA-Z0-9.@-]', '', fb)
            if clean_fb not in emails and '@' in clean_fb and clean_fb.split('@')[0]:
                emails.append(clean_fb)
        return emails

    def find_contacts(self, company_domain: str, titles: List[str], limit: int = 3, locations: List[str] = None) -> List[Dict]:
        contacts = []
        if self.apollo_key:
            contacts = self._search_apollo(company_domain, titles, limit, locations)
            
        if not contacts:
            contacts = self._search_duckduckgo_linkedin(company_domain, titles, limit)
            
        pattern = self._get_hunter_pattern(company_domain)
        
        for c in contacts:
            c['Permutations'] = [] # Default empty
            if not c.get('Email') and c.get('Name'):
                name_parts = c['Name'].split(' ')
                if len(name_parts) >= 2:
                    fn, ln = name_parts[0], name_parts[-1]
                    
                    if self.hunter_key:
                        hunter_email = self._hunter_find_email(company_domain, fn, ln)
                        if hunter_email:
                            c['Email'] = hunter_email
                            c['Source'] += " + API Extracted"
                            continue
                            
                    perms = self.build_email_permutations(fn, ln, company_domain, pattern)
                    if perms:
                        c['Email'] = perms[0]
                        c['Permutations'] = perms[1:5]
                        c['Source'] += f" + Dynamic Pattern AI"
                elif len(name_parts) == 1 and name_parts[0]:
                    fn = name_parts[0].lower().strip()
                    c['Email'] = f"{fn}@{company_domain}"
                    c['Source'] += " + Dynamic Pattern AI"
                    
        contacts.extend(self._scrape_fallback(company_domain))
        return contacts

    def _hunter_find_email(self, domain: str, first_name: str, last_name: str) -> str:
        url = f"https://api.hunter.io/v2/email-finder?domain={domain}&first_name={first_name}&last_name={last_name}&api_key={self.hunter_key}"
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                data = r.json().get('data', {})
                return data.get('email', '')
        except:
            pass
        return ""

    def _search_apollo(self, domain: str, titles: List[str], limit: int, locations: List[str]) -> List[Dict]:
        url = "https://api.apollo.io/v1/mixed_people/api_search"
        headers = {"Content-Type": "application/json", "Cache-Control": "no-cache", "X-Api-Key": self.apollo_key}
        data = {
            "q_organization_domains": domain,
            "page": 1,
            "per_page": limit,
            "person_titles": titles
        }
        if locations:
            data["person_locations"] = locations
            
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            results = response.json().get('people', [])
            
            contacts = []
            for person in results:
                raw_email = person.get('email')
                last_name = person.get('last_name') or person.get('last_name_obfuscated', '').replace('*', '')
                contacts.append({
                    "Name": f"{person.get('first_name', '')} {last_name}".strip(),
                    "Title": person.get('title'),
                    "Email": raw_email if raw_email else "",
                    "Company": person.get('organization', {}).get('name', domain),
                    "LinkedIn": person.get('linkedin_url'),
                    "Source": "Apollo.io"
                })
            return contacts
        except Exception:
            return []

    def _search_duckduckgo_linkedin(self, domain: str, titles: List[str], limit: int) -> List[Dict]:
        company = domain.split('.')[0]
        titles_query = " OR ".join([f'"{t}"' for t in titles])
        query = f'site:linkedin.com/in/ "{company}" AND ({titles_query})'
        url = "https://html.duckduckgo.com/html/"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        contacts = []
        try:
            res = requests.post(url, data={'q': query}, headers=headers, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            for a in soup.find_all('a', class_='result__url', href=True):
                link = a['href']
                if 'linkedin.com/in/' in link:
                    name = re.sub(r'\|.*', '', a.text.split('-')[0]).strip()
                    parent = a.find_parent('div', class_='result__body')
                    snippet = parent.find('a', class_='result__snippet').text if parent and parent.find('a', class_='result__snippet') else f"LinkedIn User at {company}"
                    contacts.append({
                        "Name": name,
                        "Title": snippet[:60] + "...",
                        "Email": "",
                        "Company": domain,
                        "LinkedIn": link,
                        "Source": "LinkedIn X-Ray OSINT"
                    })
                    if len(contacts) >= limit: break
            time.sleep(1)
        except Exception: pass
        return contacts

    def _scrape_fallback(self, domain: str) -> List[Dict]:
        urls = [f"http://www.{domain}", f"https://www.{domain}/contact", f"https://www.{domain}/about"]
        emails_found = set()
        regex = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
        for u in urls:
            try:
                res = requests.get(u, timeout=5, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
                if res.status_code == 200:
                    soup = BeautifulSoup(res.text, 'html.parser')
                    for mailto in soup.select('a[href^=mailto]'):
                        emails_found.add(mailto['href'].replace('mailto:', '').split('?')[0].strip().lower())
                    emails_found.update([e.lower() for e in regex.findall(res.text)])
            except: continue
        valid = ['info@', 'sales@', 'marketing@', 'contact@', 'support@', 'admin@']
        filtered = [e for e in emails_found if any(e.startswith(p) for p in valid)]
        
        contacts = []
        for e in list(filtered)[:5]:
            contacts.append({
                "Name": "Company Inbox", "Title": "Generic Routing Email",
                "Email": e, "Company": domain, "LinkedIn": "", "Source": "Web Scraper", "Permutations": []
            })
        return contacts

    def process_company_list(self, domains: List[str], titles: List[str], limit: int = 3, locations: List[str] = None) -> pd.DataFrame:
        all_contacts = []
        processed_domains = []
        for domain in domains:
            if domain not in processed_domains: # Prevent duplicates if many raw company names resolved to same domain
                contacts = self.find_contacts(domain, titles, limit, locations)
                all_contacts.extend(contacts)
                processed_domains.append(domain)
        # Sort structurally for UI
        df = pd.DataFrame(all_contacts)
        if not df.empty:
            df['AI Match Score'] = df['Title'].apply(lambda x: 99 if any(t.lower() in str(x).lower() for t in titles) else 50)
            df = df.sort_values(by='AI Match Score', ascending=False)
        return df
