"""
Authentication service - password hashing, JWT tokens, user verification.
"""
import hashlib
import time
from typing import Optional
from fastapi import Header
from database import db
from config import JWT_SECRET


def hash_password(password: str) -> str:
    """Hash password with salt"""
    salt = JWT_SECRET[:16]
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return hash_password(password) == hashed


def create_token(user_id: str) -> str:
    """Create a simple token (user_id:timestamp:signature)"""
    timestamp = str(int(time.time()))
    data = f"{user_id}:{timestamp}"
    signature = hashlib.sha256(f"{data}:{JWT_SECRET}".encode()).hexdigest()[:16]
    return f"{data}:{signature}"


def verify_token(token: str) -> Optional[str]:
    """Verify token and return user_id if valid"""
    try:
        parts = token.split(":")
        if len(parts) != 3:
            return None
        user_id, timestamp, signature = parts
        # Check signature
        data = f"{user_id}:{timestamp}"
        expected_sig = hashlib.sha256(f"{data}:{JWT_SECRET}".encode()).hexdigest()[:16]
        if signature != expected_sig:
            return None
        # Check expiration (7 days)
        if int(time.time()) - int(timestamp) > 7 * 24 * 3600:
            return None
        return user_id
    except:
        return None


async def get_current_user(authorization: Optional[str] = Header(None)) -> Optional[dict]:
    """Get current user from token"""
    if not authorization:
        return None
    
    token = authorization.replace("Bearer ", "")
    user_id = verify_token(token)
    if not user_id:
        return None
    
    user = await db.auth_users.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
    return user
