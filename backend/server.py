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
    NewsletterArticle, NewsletterArticleCreate
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
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI(title="InfoPilot API")

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
        
        return {
            "id": user["id"],
            "username": user["username"],
            "email": user.get("email"),
            "subscription_status": user.get("subscription_status", "free"),
            "profile_photo": user.get("profile_photo"),
            "is_public": user.get("is_public", False)
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
    """Update a category"""
    try:
        user = await get_user_from_token(authorization)
        
        category = await db.categories.find_one({"id": category_id, "user_id": user["id"]})
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        
        update_data = {k: v for k, v in category_data.dict().items() if v is not None}
        
        # Validate protocol if being updated
        if "protocol" in update_data:
            valid, error, _ = parse_protocol(update_data["protocol"])
            if not valid:
                raise HTTPException(status_code=400, detail=f"Invalid protocol: {error}")
        
        if update_data:
            await db.categories.update_one(
                {"id": category_id, "user_id": user["id"]},
                {"$set": update_data}
            )
        
        return {"success": True}
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Update category error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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
                
                # Check if result already exists
                existing = await db.search_results.find_one({
                    "user_id": user["id"],
                    "url": url
                })
                
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
