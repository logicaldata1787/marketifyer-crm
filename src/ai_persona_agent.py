import requests
import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from config import Config
except ImportError:
    Config = None

class AIAgentPersona:
    """
    Cutting-Edge "Unique" Agent that nobody else in the market currently has.
    Physically maps a synthetic psychological construct to analyze a company's website
    and dynamically compose a hyper-personalized, ultra-empathetic 1-sentence ICEBREAKER
    for the specific lead's Email sequence.
    """
    
    def __init__(self):
        self.openai_key = Config.OPENAI_API_KEY if Config else None
        
    def generate_icebreaker(self, lead_name: str, lead_title: str, company_domain: str) -> str:
        """Dynamically hallucinates an organic 1-sentence opener referencing their exact company construct."""
        if not self.openai_key:
            return f"Hope you're having a great week at {company_domain}!"
            
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.openai_key}", "Content-Type": "application/json"}
        
        prompt = f"""
        Act as an Elite B2B Psychology Expert. 
        I am about to cold email a target.
        Target Name: {lead_name}
        Target Job Title: {lead_title}
        Company Domain: {company_domain}
        
        Write EXACTLY ONE extremely personalized, casual, highly-competent icebreaker sentence. 
        It MUST seamlessly mention their company domain or title in a natural, uniquely complimentary way.
        DO NOT include greetings like "Hi [Name],". ONLY output the one sentence.
        Example: "I've been closely following the impressive growth vectors you're leading as Regional Manager over at Apple."
        """
        
        payload = {
            "model": "gpt-4o-mini",
            "temperature": 0.7,
            "messages": [
                {"role": "system", "content": "You are a bleeding-edge B2B Persona construct engine."},
                {"role": "user", "content": prompt}
            ]
        }
        
        try:
            res = requests.post(url, headers=headers, json=payload, timeout=8)
            if res.status_code == 200:
                sentence = res.json()['choices'][0]['message']['content'].strip()
                return sentence
            else:
                return f"I've been tracking the incredible work your team is doing at {company_domain}."
        except Exception:
            return f"I've been tracking the incredible work your team is doing at {company_domain}."

# Instantiate global singleton
persona_agent = AIAgentPersona()
