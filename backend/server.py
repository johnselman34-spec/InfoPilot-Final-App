from fastapi import FastAPI, APIRouter, HTTPException, Header, Query
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime
import asyncio
from serpapi import Client as SerpApiClient

# Import our modules
from models import (
    User, UserCreate, UserLogin, UserUpdate,
    Category, CategoryCreate, CategoryUpdate,
    SearchResult, ReactionUpdate,
    AdminSettings, AdminSettingsUpdate,
    CollateRequest, Message, MessageCreate,
    NewsletterArticle, NewsletterArticleCreate,
    MarketplaceProtocol, MarketplaceSell, MarketplacePurchase, PayoutRequest, Transaction
)
from utils import (
    hash_password, verify_password, create_access_token, verify_token,
    parse_protocol, protocol_to_search_query, contains_banned_content,
    extract_root_domain, extract_year_from_text
)
from ai_service import ai_service

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=5000)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI(title="InfoPilot API")

# Test MongoDB connection on startup
@app.on_event("startup")
async def startup_db_client():
    try:
        # Test the connection
        await client.admin.command('ping')
        logger.info("Successfully connected to MongoDB")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {str(e)}")
        logger.error(f"MongoDB URL: {mongo_url.split('@')[1] if '@' in mongo_url else mongo_url}")
        raise Exception(f"MongoDB connection failed: {str(e)}")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== AUTH ROUTES ====================

@api_router.post("/auth/register")
async def register(user_data: UserCreate):
    """Register a new user"""
    try:
        # Check if username exists
        existing = await db.users.find_one({"username": user_data.username})
        if existing:
            raise HTTPException(status_code=400, detail="Username already exists")
        
        # Check for banned content in username
        if contains_banned_content(user_data.username):
            raise HTTPException(status_code=400, detail="Username contains inappropriate content")
        
        # Create user
        user = User(
            username=user_data.username,
            email=user_data.email,
            password_hash=hash_password(user_data.password)
        )
        
        await db.users.insert_one(user.dict())
        
        # Create access token
        token = create_access_token({"user_id": user.id, "username": user.username})
        
        return {
            "success": True,
            "token": token,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "subscription_status": user.subscription_status
            }
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/auth/login")
async def login(credentials: UserLogin):
    """Login user"""
    try:
        user = await db.users.find_one({"username": credentials.username})
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        if user.get("banned", False):
            raise HTTPException(status_code=403, detail="Account has been banned")
        
        if not verify_password(credentials.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Create access token
        token = create_access_token({"user_id": user["id"], "username": user["username"]})
        
        return {
            "success": True,
            "token": token,
            "user": {
                "id": user["id"],
                "username": user["username"],
                "email": user.get("email"),
                "subscription_status": user.get("subscription_status", "free"),
                "profile_photo": user.get("profile_photo")
            }
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Admin email addresses - these get automatic admin privileges
ADMIN_EMAILS = [
    "jjspilot24@gmail.com",
    "johnselman34@gmail.com", 
    "john.1976.selman@gmail.com",
    "john@infojet.com"
]

def is_admin_email(email: str) -> bool:
    """Check if email is an admin email (case-insensitive)"""
    if not email:
        return False
    return email.lower() in [e.lower() for e in ADMIN_EMAILS]

# Google OAuth Authentication
from pydantic import BaseModel

class GoogleAuthData(BaseModel):
    email: str
    google_id: str
    name: str
    picture: Optional[str] = None

@api_router.post("/auth/google")
async def google_auth(auth_data: GoogleAuthData):
    """Authenticate with Google OAuth - auto-creates admin accounts for specified emails"""
    try:
        # Check if user exists by email
        user = await db.users.find_one({"email": {"$regex": f"^{auth_data.email}$", "$options": "i"}})
        
        # Determine admin status
        admin_status = is_admin_email(auth_data.email)
        
        if user:
            # Update Google ID if not set, and update admin status
            update_data = {
                "google_id": auth_data.google_id,
                "is_admin": admin_status
            }
            if auth_data.picture:
                update_data["profile_photo"] = auth_data.picture
                
            await db.users.update_one(
                {"id": user["id"]},
                {"$set": update_data}
            )
            user["is_admin"] = admin_status
        else:
            # Create new user from Google account
            username = auth_data.name.replace(" ", "_").lower()
            # Make username unique
            base_username = username
            counter = 1
            while await db.users.find_one({"username": username}):
                username = f"{base_username}_{counter}"
                counter += 1
            
            user = User(
                username=username,
                email=auth_data.email,
                password_hash="GOOGLE_OAUTH_USER",  # No password for Google users
                profile_photo=auth_data.picture
            )
            user_dict = user.dict()
            user_dict["google_id"] = auth_data.google_id
            user_dict["is_admin"] = admin_status
            
            await db.users.insert_one(user_dict)
            user = user_dict
        
        # Create access token
        token = create_access_token({"user_id": user["id"], "username": user["username"]})
        
        logger.info(f"Google auth successful for {auth_data.email}, admin={admin_status}")
        
        return {
            "success": True,
            "token": token,
            "user": {
                "id": user["id"],
                "username": user["username"],
                "email": auth_data.email,
                "subscription_status": user.get("subscription_status", "free"),
                "profile_photo": auth_data.picture or user.get("profile_photo"),
                "is_admin": admin_status
            }
        }
    except Exception as e:
        logger.error(f"Google auth error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Password Reset
class PasswordResetRequest(BaseModel):
    email: str
    new_password: str

@api_router.post("/auth/reset-password")
async def reset_password(request: PasswordResetRequest):
    """Reset user password by email"""
    try:
        user = await db.users.find_one({"email": {"$regex": f"^{request.email}$", "$options": "i"}})
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Hash new password
        hashed = hash_password(request.new_password)
        
        await db.users.update_one(
            {"id": user["id"]},
            {"$set": {"password_hash": hashed}}
        )
        
        return {"success": True, "message": "Password reset successfully! 🎉"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/auth/me")
async def get_current_user(authorization: Optional[str] = Header(None)):
    """Get current user from token"""
    try:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        token = authorization.split(" ")[1]
        payload = verify_token(token)
        
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = await db.users.find_one({"id": payload["user_id"]})
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check admin status by email
        is_admin = user.get("is_admin", False) or is_admin_email(user.get("email", ""))
        
        return {
            "id": user["id"],
            "username": user["username"],
            "email": user.get("email"),
            "subscription_status": user.get("subscription_status", "free"),
            "profile_photo": user.get("profile_photo"),
            "is_public": user.get("is_public", False),
            "is_admin": is_admin
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Get user error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Helper function to get user from token
async def get_user_from_token(authorization: Optional[str]) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = authorization.split(" ")[1]
    payload = verify_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = await db.users.find_one({"id": payload["user_id"]})
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user

# ==================== CATEGORY ROUTES ====================

@api_router.post("/categories")
async def create_category(category_data: CategoryCreate, authorization: Optional[str] = Header(None)):
    """Create a new category with protocol"""
    try:
        user = await get_user_from_token(authorization)
        
        # Check for banned content
        if contains_banned_content(category_data.name) or contains_banned_content(category_data.protocol):
            raise HTTPException(status_code=400, detail="Category contains inappropriate content")
        
        # Validate protocol
        valid, error, _ = parse_protocol(category_data.protocol)
        if not valid:
            raise HTTPException(status_code=400, detail=f"Invalid protocol: {error}")
        
        # Determine level
        level = 0
        if category_data.parent_id:
            parent = await db.categories.find_one({"id": category_data.parent_id, "user_id": user["id"]})
            if parent:
                level = parent["level"] + 1
        
        category = Category(
            user_id=user["id"],
            name=category_data.name,
            protocol=category_data.protocol,
            parent_id=category_data.parent_id,
            level=level,
            is_public=category_data.is_public
        )
        
        await db.categories.insert_one(category.dict())
        
        return {"success": True, "category": category.dict()}
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Create category error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/categories")
async def get_categories(authorization: Optional[str] = Header(None)):
    """Get all categories for current user"""
    try:
        user = await get_user_from_token(authorization)
        
        categories = await db.categories.find(
            {"user_id": user["id"]},
            {"_id": 0, "id": 1, "name": 1, "protocol": 1, "parent_id": 1, "level": 1, "is_public": 1, "created_at": 1}
        ).limit(100).to_list(100)
        
        return {"success": True, "categories": categories}
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Get categories error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/categories/user/{username}")
async def get_public_categories(username: str):
    """Get public categories for a specific user"""
    try:
        user = await db.users.find_one({"username": username})
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if not user.get("is_public", False):
            raise HTTPException(status_code=403, detail="User profile is private")
        
        categories = await db.categories.find({
            "user_id": user["id"],
            "is_public": True
        }, {
            "_id": 0, "id": 1, "name": 1, "protocol": 1, "parent_id": 1, "level": 1, "is_public": 1, "created_at": 1
        }).limit(100).to_list(100)
        
        return {"success": True, "categories": categories, "username": username}
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Get public categories error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.put("/categories/{category_id}")
async def update_category(category_id: str, category_data: CategoryUpdate, authorization: Optional[str] = Header(None)):
    """Update a category - FIXED to properly save changes"""
    try:
        user = await get_user_from_token(authorization)
        
        category = await db.categories.find_one({"id": category_id, "user_id": user["id"]})
        if not category:
            logger.error(f"Category not found: {category_id} for user {user['id']}")
            raise HTTPException(status_code=404, detail="Category not found")
        
        update_data = {k: v for k, v in category_data.dict().items() if v is not None}
        
        logger.info(f"Updating category {category_id} with data: {update_data}")
        
        # Validate protocol if being updated
        if "protocol" in update_data:
            valid, error, _ = parse_protocol(update_data["protocol"])
            if not valid:
                raise HTTPException(status_code=400, detail=f"Invalid protocol: {error}")
        
        if update_data:
            # Add timestamp
            update_data["updated_at"] = datetime.utcnow()
            
            result = await db.categories.update_one(
                {"id": category_id, "user_id": user["id"]},
                {"$set": update_data}
            )
            
            logger.info(f"Update result: matched={result.matched_count}, modified={result.modified_count}")
            
            if result.matched_count == 0:
                raise HTTPException(status_code=404, detail="Category not found during update")
        
        # Fetch updated category to return
        updated_category = await db.categories.find_one(
            {"id": category_id},
            {"_id": 0}
        )
        
        return {"success": True, "category": updated_category, "message": "Category updated successfully! 🎉"}
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Update category error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Protocol Debug Endpoint - Test protocols without creating categories
class ProtocolDebugRequest(BaseModel):
    protocol: str
    test_text: Optional[str] = None

@api_router.post("/protocol/debug")
async def debug_protocol(request: ProtocolDebugRequest):
    """Debug a protocol - test parsing and matching without saving anything"""
    try:
        valid, error, search_terms = parse_protocol(request.protocol)
        
        if not valid:
            return {
                "valid": False,
                "error": error,
                "search_terms": [],
                "search_query": "",
                "would_match_test": False
            }
        
        search_query = protocol_to_search_query(request.protocol)
        
        # Test against provided text if given
        would_match = False
        if request.test_text:
            test_lower = request.test_text.lower()
            for group in search_terms:
                if group['modifier'] == '^':  # Exclusion
                    for term in group['terms']:
                        if term.lower() in test_lower:
                            would_match = False
                            break
                else:
                    for term in group['terms']:
                        if term.lower() in test_lower:
                            would_match = True
                            break
        
        return {
            "valid": True,
            "error": None,
            "search_terms": search_terms,
            "search_query": search_query,
            "would_match_test": would_match,
            "message": "Protocol is valid! 🎯 Ready to find amazing results!"
        }
    except Exception as e:
        logger.error(f"Protocol debug error: {str(e)}")
        return {
            "valid": False,
            "error": str(e),
            "search_terms": [],
            "search_query": "",
            "would_match_test": False
        }

@api_router.delete("/categories/{category_id}")
async def delete_category(category_id: str, authorization: Optional[str] = Header(None)):
    """Delete a category and its search results"""
    try:
        user = await get_user_from_token(authorization)
        
        # Delete category
        result = await db.categories.delete_one({"id": category_id, "user_id": user["id"]})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Category not found")
        
        # Delete associated search results
        await db.search_results.delete_many({
            "user_id": user["id"],
            "category_ids": category_id
        })
        
        return {"success": True}
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Delete category error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== SEARCH & COLLATE ROUTES ====================

@api_router.get("/search/google")
async def google_search(q: str = Query(...)):
    """Perform a Google search using SerpAPI"""
    try:
        serpapi_key = os.getenv("SERPAPI_KEY")
        client = SerpApiClient(api_key=serpapi_key)
        
        results = client.search({
            "q": q,
            "engine": "google",
            "num": 20
        })
        
        organic_results = results.get("organic_results", [])
        
        return {
            "success": True,
            "results": organic_results
        }
    except Exception as e:
        logger.error(f"Google search error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/search/collate")
async def collate_search(request: CollateRequest, authorization: Optional[str] = Header(None)):
    """Collate search results using SerpAPI and classify with AI"""
    try:
        user = await get_user_from_token(authorization)
        
        # Get category
        category = await db.categories.find_one({"id": request.category_id, "user_id": user["id"]})
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        
        # Parse protocol
        valid, error, search_terms = parse_protocol(category["protocol"])
        if not valid:
            raise HTTPException(status_code=400, detail=f"Invalid protocol: {error}")
        
        # Convert protocol to search query
        protocol_query = protocol_to_search_query(category["protocol"])
        
        # Combine with user's search query
        final_query = f"{request.search_query} {protocol_query}" if request.search_query else protocol_query
        
        # Search with SerpAPI
        serpapi_key = os.getenv("SERPAPI_KEY")
        client = SerpApiClient(api_key=serpapi_key)
        
        results = client.search({
            "q": final_query,
            "engine": "google",
            "num": 20
        })
        
        organic_results = results.get("organic_results", [])
        
        # Batch query: Get all existing URLs upfront to avoid N+1 queries
        all_urls = [result.get("link", "") for result in organic_results]
        existing_results = await db.search_results.find({
            "user_id": user["id"],
            "url": {"$in": all_urls}
        }, {"url": 1, "id": 1, "category_ids": 1}).to_list(len(all_urls))
        
        # Create a lookup dictionary for O(1) access
        existing_by_url = {result["url"]: result for result in existing_results}
        
        # Process each result
        processed_count = 0
        for result in organic_results:
            try:
                title = result.get("title", "")
                snippet = result.get("snippet", "")
                url = result.get("link", "")
                
                # Check for banned content
                if contains_banned_content(title) or contains_banned_content(snippet):
                    continue
                
                # Classify with AI
                classification = await ai_service.classify_article(title, snippet, url)
                
                if classification["contains_banned"]:
                    continue
                
                # Check if result matches protocol
                matches = await ai_service.check_protocol_matches_result(search_terms, title, snippet)
                
                if not matches:
                    continue
                
                # Extract metadata
                root_domain = extract_root_domain(url)
                year = extract_year_from_text(f"{title} {snippet}")
                
                # Check if result already exists (using batched lookup)
                existing = existing_by_url.get(url)
                
                if existing:
                    # Update category_ids if not already included
                    if request.category_id not in existing["category_ids"]:
                        await db.search_results.update_one(
                            {"id": existing["id"]},
                            {"$push": {"category_ids": request.category_id}}
                        )
                else:
                    # Create new search result
                    search_result = SearchResult(
                        user_id=user["id"],
                        category_ids=[request.category_id],
                        url=url,
                        title=title,
                        snippet=snippet,
                        article_type=classification["article_type"],
                        root_domain=root_domain,
                        year=year
                    )
                    
                    await db.search_results.insert_one(search_result.dict())
                
                processed_count += 1
                
            except Exception as e:
                logger.error(f"Error processing result: {str(e)}")
                continue
        
        return {
            "success": True,
            "processed_count": processed_count,
            "message": f"Collated {processed_count} results for category {category['name']}"
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Collate error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/search/results")
async def get_search_results(
    category_ids: Optional[str] = Query(None),
    article_type: Optional[str] = Query(None),
    root_domain: Optional[str] = Query(None),
    year: Optional[int] = Query(None),
    search_text: Optional[str] = Query(None),
    page: int = Query(1),
    authorization: Optional[str] = Header(None)
):
    """Get search results with filters"""
    try:
        user = await get_user_from_token(authorization)
        
        # Build query
        query = {"user_id": user["id"]}
        
        if category_ids:
            cat_list = category_ids.split(",")
            query["category_ids"] = {"$in": cat_list}
        
        if article_type:
            query["article_type"] = article_type
        
        if root_domain:
            query["root_domain"] = root_domain
        
        if year:
            query["year"] = year
        
        if search_text:
            query["$or"] = [
                {"title": {"$regex": search_text, "$options": "i"}},
                {"snippet": {"$regex": search_text, "$options": "i"}}
            ]
        
        # Get admin settings for pagination
        admin_settings = await db.admin_settings.find_one()
        results_per_page = admin_settings.get("search_results_per_page", 20) if admin_settings else 20
        
        # Check subscription for page limit
        if user.get("subscription_status") == "free":
            unpaid_limit = admin_settings.get("unpaid_page_limit", 1) if admin_settings else 1
            if page > unpaid_limit:
                raise HTTPException(status_code=403, detail="Subscribe to access more pages")
        
        skip = (page - 1) * results_per_page
        
        results = await db.search_results.find(
            query,
            {"_id": 0, "id": 1, "url": 1, "title": 1, "snippet": 1, "article_type": 1, "root_domain": 1, 
             "year": 1, "category_ids": 1, "created_at": 1, "likes": 1, "loves": 1, "funnys": 1, 
             "sads": 1, "cautions": 1, "spams": 1, "bests": 1}
        ).skip(skip).limit(results_per_page).to_list(results_per_page)
        total = await db.search_results.count_documents(query)
        
        return {
            "success": True,
            "results": results,
            "total": total,
            "page": page,
            "per_page": results_per_page,
            "total_pages": (total + results_per_page - 1) // results_per_page
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Get search results error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/search/results/{result_id}/react")
async def react_to_result(result_id: str, reaction: ReactionUpdate, authorization: Optional[str] = Header(None)):
    """React to a search result (like, love, funny, sad, caution, spam, best)"""
    try:
        user = await get_user_from_token(authorization)
        
        result = await db.search_results.find_one({"id": result_id})
        if not result:
            raise HTTPException(status_code=404, detail="Result not found")
        
        # Update reaction count
        field = f"{reaction.reaction_type}s"
        await db.search_results.update_one(
            {"id": result_id},
            {"$inc": {field: 1}}
        )
        
        return {"success": True}
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"React to result error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/search/results/bulk")
async def delete_search_results(
    category_id: str = Query(...),
    authorization: Optional[str] = Header(None)
):
    """Delete all search results for a category"""
    try:
        user = await get_user_from_token(authorization)
        
        result = await db.search_results.delete_many({
            "user_id": user["id"],
            "category_ids": category_id
        })
        
        return {
            "success": True,
            "deleted_count": result.deleted_count
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Delete search results error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== USER PROFILE ROUTES ====================

@api_router.put("/users/profile")
async def update_profile(update_data: UserUpdate, authorization: Optional[str] = Header(None)):
    """Update user profile"""
    try:
        user = await get_user_from_token(authorization)
        
        update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
        
        if update_dict:
            await db.users.update_one(
                {"id": user["id"]},
                {"$set": update_dict}
            )
        
        return {"success": True}
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Update profile error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/users/subscribe")
async def subscribe_user(authorization: Optional[str] = Header(None)):
    """Update user subscription status to paid"""
    try:
        user = await get_user_from_token(authorization)
        
        await db.users.update_one(
            {"id": user["id"]},
            {"$set": {"subscription_status": "paid"}}
        )
        
        return {"success": True, "message": "Subscription activated"}
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Subscribe error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== ADMIN ROUTES ====================

@api_router.get("/admin/settings")
async def get_admin_settings():
    """Get admin settings"""
    try:
        settings = await db.admin_settings.find_one()
        
        if not settings:
            # Create default settings
            default_settings = AdminSettings()
            await db.admin_settings.insert_one(default_settings.dict())
            return {"success": True, "settings": default_settings.dict()}
        
        return {"success": True, "settings": settings}
        
    except Exception as e:
        logger.error(f"Get admin settings error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== MARKETPLACE ROUTES ====================

# PayPal credentials from user's document
PAYPAL_CLIENT_ID = os.environ.get('PAYPAL_CLIENT_ID', 'BAABmhMWqe1WrfJkqJ7RRzEZwoAfxSF2bclm8_HY2BuU9C-7pnakTdjFVCvSJyWh63-wUWmKN1cT1hdMIY')
PAYPAL_HOSTED_BUTTON_ID = '765S46VPPEP5C'
MARKETPLACE_PLATFORM_FEE = 0.10  # 10% to platform
MARKETPLACE_SELLER_SHARE = 0.90  # 90% to seller
MIN_PAYOUT_THRESHOLD = 1.00  # PayPal minimum

@api_router.get("/marketplace/protocols")
async def get_marketplace_protocols(
    sort: str = Query("popularity", regex="^(popularity|price|recent)$"),
    min_price: float = Query(1.01, ge=1.01),
    max_price: float = Query(2.99, le=2.99),
    limit: int = Query(100, le=500)
):
    """Get all protocols for sale on the marketplace - THE WORLD'S GREATEST PROTOCOL BAZAAR! 🎪"""
    try:
        # Build sort criteria
        sort_criteria = {}
        if sort == "popularity":
            sort_criteria = {"purchase_count": -1}
        elif sort == "price":
            sort_criteria = {"price": 1}
        else:  # recent
            sort_criteria = {"created_at": -1}
        
        # Query protocols for sale
        protocols_cursor = db.marketplace_protocols.find({
            "is_for_sale": True,
            "price": {"$gte": min_price, "$lte": max_price}
        }).sort(list(sort_criteria.items())).limit(limit)
        
        protocols = []
        async for protocol in protocols_cursor:
            # Get category and user info
            category = await db.categories.find_one({"id": protocol["category_id"]})
            user = await db.users.find_one({"id": protocol["user_id"]})
            
            protocols.append({
                "id": str(protocol.get("id", protocol.get("_id"))),
                "name": category["name"] if category else "Mystery Protocol 🎭",
                "protocol_string": category["protocol"] if category else "",
                "user_id": protocol["user_id"],
                "username": user["username"] if user else "Anonymous Genius",
                "price": protocol["price"],
                "is_for_sale": protocol["is_for_sale"],
                "category_id": protocol["category_id"],
                "description": protocol.get("description", "A protocol so good, words fail us! 🚀"),
                "purchase_count": protocol.get("purchase_count", 0),
                "location": protocol.get("location"),
                "created_at": protocol.get("created_at").isoformat() if protocol.get("created_at") else None
            })
        
        return {
            "protocols": protocols, 
            "total": len(protocols),
            "message": f"🎉 {len(protocols)} AMAZING protocols available! Get 'em while they're hot!"
        }
        
    except Exception as e:
        logger.error(f"Marketplace load error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/marketplace/sell")
async def list_protocol_for_sale(
    data: MarketplaceSell,
    authorization: Optional[str] = Header(None)
):
    """List a protocol for sale - Become a PROTOCOL MILLIONAIRE* today! 💰"""
    try:
        user = await get_user_from_token(authorization)
        
        # Verify category belongs to user
        category = await db.categories.find_one({
            "id": data.category_id,
            "user_id": user["id"]
        })
        
        if not category:
            raise HTTPException(status_code=404, detail="Category not found or not owned by you. Nice try though! 😏")
        
        # Check if already listed
        existing = await db.marketplace_protocols.find_one({
            "category_id": data.category_id,
            "user_id": user["id"]
        })
        
        if existing:
            # Update existing listing
            await db.marketplace_protocols.update_one(
                {"_id": existing["_id"]},
                {"$set": {
                    "price": data.price,
                    "description": data.description,
                    "is_for_sale": True,
                    "updated_at": datetime.utcnow()
                }}
            )
            return {
                "success": True,
                "message": "Protocol listing updated! Time to get PAID! 💸",
                "id": str(existing["_id"])
            }
        else:
            # Create new listing
            protocol_doc = {
                "id": str(uuid.uuid4()),
                "category_id": data.category_id,
                "user_id": user["id"],
                "price": data.price,
                "description": data.description or "A magnificent protocol crafted with love ❤️",
                "is_for_sale": True,
                "purchase_count": 0,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "location": None  # Will be set based on user location if available
            }
            
            result = await db.marketplace_protocols.insert_one(protocol_doc)
            return {
                "success": True,
                "message": f"🎉 Protocol listed for ${data.price}! You're officially a protocol entrepreneur!",
                "id": str(result.inserted_id)
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Marketplace sell error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/marketplace/purchase")
async def purchase_protocol(
    data: MarketplacePurchase,
    authorization: Optional[str] = Header(None)
):
    """Purchase a protocol - Best investment since sliced bread! 🍞"""
    try:
        buyer = await get_user_from_token(authorization)
        
        # Get the protocol listing
        protocol = await db.marketplace_protocols.find_one({"id": data.protocol_id})
        if not protocol:
            raise HTTPException(status_code=404, detail="Protocol not found. Maybe it's TOO popular? 🤔")
        
        if not protocol.get("is_for_sale"):
            raise HTTPException(status_code=400, detail="This protocol isn't for sale anymore. Darn! 😢")
        
        if protocol["user_id"] == buyer["id"]:
            raise HTTPException(status_code=400, detail="You can't buy your own protocol, silly! 🙃")
        
        # Calculate amounts
        total_amount = protocol["price"]
        seller_amount = round(total_amount * MARKETPLACE_SELLER_SHARE, 2)
        platform_amount = round(total_amount * MARKETPLACE_PLATFORM_FEE, 2)
        
        # Create transaction record
        transaction = Transaction(
            buyer_id=buyer["id"],
            seller_id=protocol["user_id"],
            protocol_id=data.protocol_id,
            amount=total_amount,
            seller_amount=seller_amount,
            platform_amount=platform_amount,
            status="pending"
        )
        
        await db.transactions.insert_one(transaction.dict())
        
        # Generate PayPal payment URL
        paypal_url = f"https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id={PAYPAL_HOSTED_BUTTON_ID}&amount={total_amount}&custom={transaction.id}"
        
        return {
            "success": True,
            "transaction_id": transaction.id,
            "paypal_url": paypal_url,
            "amount": total_amount,
            "seller_gets": seller_amount,
            "platform_fee": platform_amount,
            "message": f"💰 About to unlock PURE GOLD for just ${total_amount}! Creator gets ${seller_amount} (90%), we keep ${platform_amount} (10%) for coffee ☕"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Marketplace purchase error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/marketplace/payout")
async def get_payout_info(authorization: Optional[str] = Header(None)):
    """Get user's payout balance - Count your riches! 💎"""
    try:
        user = await get_user_from_token(authorization)
        
        # Calculate total earnings from completed transactions
        transactions = await db.transactions.find({
            "seller_id": user["id"],
            "status": "completed"
        }).to_list(1000)
        
        total_earned = sum(t.get("seller_amount", 0) for t in transactions)
        
        # Get pending payouts
        pending_payout = await db.pending_payouts.find_one({"user_id": user["id"]})
        accumulated = pending_payout.get("amount", 0) if pending_payout else 0
        
        can_request_payout = accumulated >= MIN_PAYOUT_THRESHOLD
        
        return {
            "total_earned": round(total_earned, 2),
            "accumulated_balance": round(accumulated, 2),
            "min_payout_threshold": MIN_PAYOUT_THRESHOLD,
            "can_request_payout": can_request_payout,
            "transactions_count": len(transactions),
            "message": f"💰 You've earned ${round(total_earned, 2)} total! " + 
                      (f"Ready to cash out ${round(accumulated, 2)}! 🎉" if can_request_payout else 
                       f"Accumulate ${round(MIN_PAYOUT_THRESHOLD - accumulated, 2)} more to request payout! 📈")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Payout info error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/marketplace/payout")
async def request_payout(
    data: PayoutRequest,
    authorization: Optional[str] = Header(None)
):
    """Request a payout - Time to get PAID! 💵"""
    try:
        user = await get_user_from_token(authorization)
        
        # Get accumulated balance
        pending_payout = await db.pending_payouts.find_one({"user_id": user["id"]})
        accumulated = pending_payout.get("amount", 0) if pending_payout else 0
        
        if accumulated < MIN_PAYOUT_THRESHOLD:
            raise HTTPException(
                status_code=400, 
                detail=f"Minimum payout is ${MIN_PAYOUT_THRESHOLD}. You have ${accumulated}. Keep selling! 📈"
            )
        
        # Update user's PayPal email
        await db.users.update_one(
            {"id": user["id"]},
            {"$set": {"paypal_email": data.paypal_email}}
        )
        
        # Create payout request
        payout_request = {
            "user_id": user["id"],
            "paypal_email": data.paypal_email,
            "amount": accumulated,
            "status": "pending",
            "created_at": datetime.utcnow()
        }
        
        await db.payout_requests.insert_one(payout_request)
        
        # Reset accumulated balance
        await db.pending_payouts.update_one(
            {"user_id": user["id"]},
            {"$set": {"amount": 0}},
            upsert=True
        )
        
        return {
            "success": True,
            "amount": accumulated,
            "paypal_email": data.paypal_email,
            "message": f"🎉 Payout of ${accumulated} requested to {data.paypal_email}! Money incoming! 💸"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Payout request error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Import uuid for transaction IDs
import uuid

# ==================== HEALTH CHECK ====================

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "InfoPilot API"}

@api_router.get("/")
async def root():
    return {"message": "InfoPilot API", "version": "1.0.0"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
