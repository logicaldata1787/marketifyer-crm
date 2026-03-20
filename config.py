import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_secret(key, default=None):
    val = os.getenv(key)
    if not val:
        try:
            import streamlit as st
            if key in st.secrets:
                return st.secrets[key]
        except Exception:
            pass
    return val if val else default

class Config:
    # LLM Settings
    OPENAI_API_KEY = get_secret("OPENAI_API_KEY")

    # API Keys for Data Enrichment and Web Search
    APOLLO_API_KEY = get_secret("APOLLO_API_KEY")
    HUNTER_API_KEY = get_secret("HUNTER_API_KEY")
    TAVILY_API_KEY = get_secret("TAVILY_API_KEY")

    # Email Settings
    SMTP_HOST = get_secret("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(get_secret("SMTP_PORT", 587))
    SMTP_USER = get_secret("SMTP_USER")
    SMTP_PASSWORD = get_secret("SMTP_PASSWORD")

    @classmethod
    def validate_keys(cls):
        """Validate that critical keys are present"""
        missing = []
        if not cls.OPENAI_API_KEY:
            missing.append("OPENAI_API_KEY")
        if not cls.APOLLO_API_KEY and not cls.HUNTER_API_KEY:
            print("Warning: No contact enrichment API keys found. Web scraping fallback will be used, which is less reliable.")
        
        return missing

# -----------------------------------------------------
# SUPABASE HYBRID INTEGRATION (Optional Commercial DB)
# -----------------------------------------------------
Config.SUPABASE_URL = get_secret("SUPABASE_URL")
Config.SUPABASE_KEY = get_secret("SUPABASE_KEY")

try:
    from supabase import create_client, Client
    if Config.SUPABASE_URL and Config.SUPABASE_KEY:
        supabase_client: Client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
    else:
        supabase_client = None
except ImportError:
    supabase_client = None

# -----------------------------------------------------
# NATIVE RAW POSTGRES Q-BYPASS INJECTION
# -----------------------------------------------------
def get_db_connection():
    try:
        import psycopg2
        conn = psycopg2.connect(
            host="db.ohgrvdsrwesrpjzfmbjh.supabase.co",
            port=5432,
            dbname="postgres",
            user="postgres",
            password="Pandey@123$!"
        )
        conn.autocommit = True
        return conn
    except Exception as e:
        print(f"FATAL POSTGRES RAW ROUTE ERROR: {e}")
        return None
