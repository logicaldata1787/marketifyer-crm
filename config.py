import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # LLM Settings
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    # API Keys for Data Enrichment and Web Search
    APOLLO_API_KEY = os.getenv("APOLLO_API_KEY")
    HUNTER_API_KEY = os.getenv("HUNTER_API_KEY")
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

    # Email Settings
    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    SMTP_USER = os.getenv("SMTP_USER")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

    @classmethod
    def validate_keys(cls):
        """Validate that critical keys are present"""
        missing = []
        if not cls.OPENAI_API_KEY:
            missing.append("OPENAI_API_KEY")
        if not cls.APOLLO_API_KEY and not cls.HUNTER_API_KEY:
            print("Warning: No contact enrichment API keys found. Web scraping fallback will be used, which is less reliable.")
        
        return missing
