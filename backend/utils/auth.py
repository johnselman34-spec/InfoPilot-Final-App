"""Authentication utilities and dependencies"""
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from typing import Optional
from utils.config import JWT_SECRET, JWT_ALGORITHM
from utils.database import db

security = HTTPBearer(auto_error=False)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[dict]:
    """Get current user from JWT token - returns None if no valid token"""
    if not credentials:
        return None
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user = await db.users.find_one({"id": payload["user_id"]}, {"_id": 0})
        return user
    except:
        return None

async def require_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Require valid user - raises 401 if not authenticated"""
    user = await get_current_user(credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user

async def require_admin(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Require admin user - raises 403 if not admin"""
    user = await require_user(credentials)
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

async def require_paid_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Require paid user - raises 403 if not paid"""
    user = await require_user(credentials)
    if not user.get("is_paid") and not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Paid subscription required")
    return user
