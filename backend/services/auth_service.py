"""
InfoPilot Explorer - Authentication Service
Handles user authentication, token management, and password hashing
"""
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from config import db, logger


class AuthService:
    """Authentication and user management service"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify a password against its hash"""
        return AuthService.hash_password(password) == hashed
    
    @staticmethod
    def generate_token() -> str:
        """Generate a secure random token"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    async def create_session(user_id: str) -> str:
        """Create a new session and return the token"""
        token = AuthService.generate_token()
        await db.sessions.insert_one({
            "token": token,
            "user_id": user_id,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(days=30)
        })
        return token
    
    @staticmethod
    async def validate_token(token: str) -> Optional[Dict[str, Any]]:
        """Validate a token and return the associated user"""
        if not token:
            return None
        
        session = await db.sessions.find_one({
            "token": token,
            "expires_at": {"$gt": datetime.utcnow()}
        })
        
        if not session:
            return None
        
        user = await db.users.find_one({"_id": session["user_id"]})
        return user
    
    @staticmethod
    async def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
        """Get user by email (case-insensitive)"""
        import re
        return await db.users.find_one({
            "email": {"$regex": f"^{re.escape(email)}$", "$options": "i"}
        })
    
    @staticmethod
    async def get_user_by_google_id(google_id: str) -> Optional[Dict[str, Any]]:
        """Get user by Google ID"""
        return await db.users.find_one({"google_id": google_id})
    
    @staticmethod
    async def create_user(email: str, username: str, password: Optional[str] = None, 
                         google_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a new user"""
        user_data = {
            "email": email.lower(),
            "username": username,
            "callsign": username,
            "is_admin": False,
            "subscription_active": False,
            "created_at": datetime.utcnow()
        }
        
        if password:
            user_data["hashed_password"] = AuthService.hash_password(password)
        
        if google_id:
            user_data["google_id"] = google_id
        
        result = await db.users.insert_one(user_data)
        user_data["_id"] = result.inserted_id
        return user_data
    
    @staticmethod
    async def update_user_google_id(user_id, google_id: str):
        """Update user's Google ID"""
        await db.users.update_one(
            {"_id": user_id},
            {"$set": {"google_id": google_id}}
        )
    
    @staticmethod
    def format_user_response(user: Dict[str, Any]) -> Dict[str, Any]:
        """Format user data for API response"""
        return {
            "id": str(user["_id"]),
            "email": user.get("email", ""),
            "username": user.get("username", ""),
            "callsign": user.get("callsign", user.get("username", "")),
            "is_admin": user.get("is_admin", False),
            "subscription_active": user.get("subscription_active", False),
            "ultimate_search_public": user.get("ultimate_search_public", False)
        }
