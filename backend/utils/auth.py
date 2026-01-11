"""
Authentication utilities
"""
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer(auto_error=False)

# In-memory token store
active_tokens: Dict[str, Dict[str, Any]] = {}

def hash_password(password: str) -> str:
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def generate_token() -> str:
    """Generate a secure random token"""
    return secrets.token_urlsafe(32)

def create_session(user_id: str, user_data: dict) -> str:
    """Create a new session and return token"""
    token = generate_token()
    active_tokens[token] = {
        "user_id": user_id,
        "user": user_data,
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(days=7)
    }
    return token

def get_session(token: str) -> Optional[dict]:
    """Get session data for a token"""
    session = active_tokens.get(token)
    if session and session["expires_at"] > datetime.utcnow():
        return session
    return None

def invalidate_session(token: str):
    """Invalidate a session"""
    if token in active_tokens:
        del active_tokens[token]
