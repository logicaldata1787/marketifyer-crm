import time
from email_validator import validate_email, EmailNotValidError

def verify_email(email: str) -> bool:
    if not email or not isinstance(email, str):
        return False
    try:
        # Validate syntax and check deliverability (MX records)
        validate_email(email, check_deliverability=True)
        return True
    except EmailNotValidError:
        return False
