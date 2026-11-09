import re

MIN_PASSWORD_LENGTH = 12


def validate_password_strength(pwd: str) -> str:
    """Enforce the platform password policy and return the password unchanged.

    Raises ValueError with a human-readable message when a rule is violated.
    """
    if len(pwd) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters in length")
    if not re.search(r"[A-Z]", pwd):
        raise ValueError("Password must contain at least one uppercase letter")
    if not re.search(r"[a-z]", pwd):
        raise ValueError("Password must contain at least one lowercase letter")
    if not re.search(r"\d", pwd):
        raise ValueError("Password must contain at least one digit")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", pwd):
        raise ValueError("Password must contain at least one special character")
    return pwd
