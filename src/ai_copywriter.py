from openai import OpenAI
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config

def generate_email_template(prompt: str) -> tuple[str, str]:
    """Generates a subject line and email body using OpenAI."""
    api_key = Config.OPENAI_API_KEY
    if not api_key or api_key == "your_openai_api_key_here":
        return "No OpenAI API Key Found", "Please set OPENAI_API_KEY securely in your .env file to use the AI copywriter."
        
    try:
        client = OpenAI(api_key=api_key)
        
        sys_prompt = "You are an expert B2B cold email copywriter. Keep emails short, punchy, and highly converting. Use {{name}} for the recipient's name and {{company}} for their company name. Return exactly two lines separated by exactly 'BODY:' where the first line is the subject."
        user_message = f"Write a fantastic cold email for the following product/service offering: {prompt}"
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=300
        )
        
        text = response.choices[0].message.content.strip()
        if "BODY:" in text:
            parts = text.split("BODY:", 1)
            subject = parts[0].replace("Subject:", "").replace("SUBJECT:", "").strip()
            body = parts[1].strip().replace("\n", "<br>")
            return subject, body
        else:
            return "Custom Outreach", text.replace("\n", "<br>")
            
    except Exception as e:
        return "AI Generation Error", str(e)
