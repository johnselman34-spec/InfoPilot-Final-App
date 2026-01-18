"""
InfoPilot Explorer - Authentication Utilities
JWT token handling, password hashing, and user verification
"""
import hashlib
import secrets
from typing import Dict, Optional
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from utils.db import db

security = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


def generate_token() -> str:
    """Generate a secure random token."""
    return secrets.token_urlsafe(32)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[Dict]:
    """Get the current user from the auth token."""
    if not credentials:
        return None
    token = credentials.credentials
    session = await db.sessions.find_one({"token": token})
    if not session:
        return None
    user = await db.users.find_one({"id": session["user_id"]}, {"_id": 0})
    return user


async def require_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    """Require a valid authenticated user."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required")
    token = credentials.credentials
    session = await db.sessions.find_one({"token": token})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = await db.users.find_one({"id": session["user_id"]}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


async def require_admin(user: Dict = Depends(require_user)) -> Dict:
    """Require admin privileges."""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
