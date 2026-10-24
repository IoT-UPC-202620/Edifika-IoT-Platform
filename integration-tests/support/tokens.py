"""JWT token generation for Edifika integration tests."""

from datetime import datetime, timezone, timedelta
import os
import jwt

SECRET = os.environ.get("JWT_SECRET", "e2e-secret-key-must-be-at-least-32-characters-long")


def user(user_id: int, admin: bool = False) -> str:
    """Generate an HS256 JWT for the specified user."""
    now = datetime.now(timezone.utc)
    roles = ["ADMIN"] if admin else ["OWNER", "RESIDENT"]
    sub = f"admin{user_id}@edifika.com" if admin else f"resident{user_id}@edifika.com"
    payload = {
        "sub": sub,
        "user_id": int(user_id),
        "roles": roles,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=1)).timestamp()),
    }
    return jwt.encode(payload, SECRET, algorithm="HS256")
