from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
from bson import ObjectId
import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from googleapiclient.discovery import build
import openai
import re

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'infopilot_db')]

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-this')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# Security
security = HTTPBearer()

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

# ==================== Models ====================

class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[EmailStr] = None

class UserLogin(BaseModel):
    username: str
    password: str

class User(BaseModel):
    id: str
    username: str
    email: Optional[str] = None
    isPaid: bool = False
    isAdmin: bool = False
    subscriptionStatus: Optional[str] = None
    subscriptionPrice: float = 0.99
    createdAt: datetime = Field(default_factory=datetime.utcnow)

class Token(BaseModel):
    access_token: str
    token_type: str
    user: User

class Protocol(BaseModel):
    id: Optional[str] = None
    name: str
    booleanExpression: str
    categoryId: str
    userId: str
    isPublic: bool = True
    createdAt: datetime = Field(default_factory=datetime.utcnow)

class Category(BaseModel):
    id: Optional[str] = None
    name: str
    level: int = 0
    parentId: Optional[str] = None
    userId: str
    isPublic: bool = True
    protocolId: Optional[str] = None
    createdAt: datetime = Field(default_factory=datetime.utcnow)

class SearchResultItem(BaseModel):
    title: str
    url: str
    snippet: str
    displayLink: str
    classification: Optional[str] = None

class SearchRequest(BaseModel):
    query: str
    page: int = 1
    num: int = 10

class CollateRequest(BaseModel):
    query: str
    userId: str

class ClassifyRequest(BaseModel):
    content: str
    url: str

# ==================== Helper Functions ====================

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    user["id"] = str(user["_id"])
    return User(**user)

def parse_protocol(protocol: str) -> List[str]:
    """Parse InfoJet 2.0 Boolean protocol into Google search terms"""
    # Remove special characters and extract terms
    terms = []
    
    # Find all groups in parentheses
    groups = re.findall(r'\(([^)]+)\)', protocol)
    
    for group in groups:
        # Check if it's an exclusion (^) or inclusion (+)
        if protocol.find(f'({group})^') != -1:
            # Exclusion - add NOT operator
            words = [w.strip() for w in group.split(' or ')]
            for word in words:
                terms.append(f'-{word}')
        elif protocol.find(f'({group})+') != -1:
            # Inclusion - these must all appear
            words = [w.strip() for w in group.split(' or ')]
            terms.extend([f'+{word}' for word in words])
        else:
            # Regular AND/OR logic
            words = [w.strip() for w in group.split(' or ')]
            if len(words) > 1:
                terms.append(' OR '.join(f'"{w}"' for w in words))
            else:
                terms.extend(words)
    
    return terms

def build_google_query(protocol: str) -> str:
    """Convert InfoJet 2.0 protocol to Google Custom Search query"""
    terms = parse_protocol(protocol)
    return ' '.join(terms)

async def classify_content(content: str, url: str) -> str:
    """Classify web content using AI"""
    try:
        # Get Emergent LLM key
        llm_key = os.environ.get('EMERGENT_LLM_KEY', 'sk-emergent-0FbE304C72f9bBd969')
        
        openai.api_key = llm_key
        openai.base_url = "https://llm.proxy.emergentagent.com/v1"
        
        prompt = f"""Classify the following web content into ONE of these categories:
1. Informative Ph.D - Must contain (Ph.D. or PhD or D.Phil. or Dr.) and be at least 1500 words, and contain phrases like "there are", "may have", "this type", "is easily", etc.
2. Informative - Contains analytical language: "there are", "may have", "this kind", "it is", "is more", etc.
3. News Article - Contains "news", "story", "news story" multiple times, recent events
4. Blog - Contains "blog" in title or multiple times in content
5. Forum - Contains "forum" in title
6. Personal Report (collected) - First-person narrative with "I" appearing 3+ times in paragraphs with 75+ words

Content URL: {url}
Content snippet: {content[:1000]}...

Respond with ONLY the category name, nothing else."""
        
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a content classification expert."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=50,
            temperature=0.3
        )
        
        classification = response.choices[0].message.content.strip()
        return classification
    except Exception as e:
        logger.error(f"Classification error: {e}")
        return "News Article"  # Default classification

# ==================== Authentication Routes ====================

@api_router.post("/auth/register", response_model=Token)
async def register(user_data: UserCreate):
    # Check if username exists
    existing_user = await db.users.find_one({"username": user_data.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    user_dict = {
        "username": user_data.username,
        "password": hashed_password,
        "email": user_data.email,
        "isPaid": False,
        "isAdmin": False,
        "subscriptionStatus": None,
        "subscriptionPrice": 0.99,
        "createdAt": datetime.utcnow()
    }
    
    result = await db.users.insert_one(user_dict)
    user_dict["id"] = str(result.inserted_id)
    user_dict.pop("password")
    
    # Create access token
    access_token = create_access_token(data={"sub": str(result.inserted_id)})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": User(**user_dict)
    }

@api_router.post("/auth/login", response_model=Token)
async def login(user_data: UserLogin):
    # Find user
    user = await db.users.find_one({"username": user_data.username})
    if not user or not verify_password(user_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    user["id"] = str(user["_id"])
    user.pop("password")
    
    # Create access token
    access_token = create_access_token(data={"sub": str(user["_id"])})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": User(**user)
    }

@api_router.get("/auth/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

# ==================== Category Routes ====================

@api_router.post("/categories")
async def create_category(category: Category, current_user: User = Depends(get_current_user)):
    category_dict = category.dict(exclude={"id"})
    category_dict["userId"] = current_user.id
    category_dict["createdAt"] = datetime.utcnow()
    
    result = await db.categories.insert_one(category_dict)
    category_dict["id"] = str(result.inserted_id)
    
    return {"success": True, "category": category_dict}

@api_router.get("/categories")
async def get_categories(current_user: User = Depends(get_current_user)):
    categories = await db.categories.find({"userId": current_user.id}).to_list(1000)
    for cat in categories:
        cat["id"] = str(cat["_id"])
        cat.pop("_id")
    return {"success": True, "categories": categories}

@api_router.get("/categories/public")
async def get_public_categories(skip: int = 0, limit: int = 100):
    categories = await db.categories.find({"isPublic": True}).skip(skip).limit(limit).to_list(1000)
    for cat in categories:
        cat["id"] = str(cat["_id"])
        cat.pop("_id")
    return {"success": True, "categories": categories}

@api_router.delete("/categories/{category_id}")
async def delete_category(category_id: str, current_user: User = Depends(get_current_user)):
    result = await db.categories.delete_one({"_id": ObjectId(category_id), "userId": current_user.id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"success": True, "message": "Category deleted"}

# ==================== Protocol Routes ====================

@api_router.post("/protocols")
async def create_protocol(protocol: Protocol, current_user: User = Depends(get_current_user)):
    protocol_dict = protocol.dict(exclude={"id"})
    protocol_dict["userId"] = current_user.id
    protocol_dict["createdAt"] = datetime.utcnow()
    
    result = await db.protocols.insert_one(protocol_dict)
    protocol_dict["id"] = str(result.inserted_id)
    
    # Update category with protocol ID
    await db.categories.update_one(
        {"_id": ObjectId(protocol.categoryId)},
        {"$set": {"protocolId": str(result.inserted_id)}}
    )
    
    return {"success": True, "protocol": protocol_dict}

@api_router.get("/protocols")
async def get_protocols(current_user: User = Depends(get_current_user)):
    protocols = await db.protocols.find({"userId": current_user.id}).to_list(1000)
    for proto in protocols:
        proto["id"] = str(proto["_id"])
        proto.pop("_id")
    return {"success": True, "protocols": protocols}

@api_router.delete("/protocols/{protocol_id}")
async def delete_protocol(protocol_id: str, current_user: User = Depends(get_current_user)):
    result = await db.protocols.delete_one({"_id": ObjectId(protocol_id), "userId": current_user.id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Protocol not found")
    return {"success": True, "message": "Protocol deleted"}

# ==================== Search Routes ====================

@api_router.post("/search")
async def search_google(search_req: SearchRequest, current_user: User = Depends(get_current_user)):
    """Search using Google Custom Search API"""
    try:
        # Get API credentials from environment
        api_key = os.environ.get('GOOGLE_API_KEY', '')
        cx = os.environ.get('GOOGLE_CX', '')
        
        if not api_key or not cx:
            raise HTTPException(status_code=500, detail="Google API credentials not configured")
        
        # Build Google Custom Search service
        service = build("customsearch", "v1", developerKey=api_key)
        
        # Calculate start index
        start_index = (search_req.page - 1) * search_req.num + 1
        
        # Execute search
        result = service.cse().list(
            q=search_req.query,
            cx=cx,
            start=start_index,
            num=min(search_req.num, 10)  # Google limits to 10 per request
        ).execute()
        
        items = result.get('items', [])
        search_info = result.get('searchInformation', {})
        
        return {
            "success": True,
            "results": [
                {
                    "title": item.get('title', ''),
                    "url": item.get('link', ''),
                    "snippet": item.get('snippet', ''),
                    "displayLink": item.get('displayLink', ''),
                }
                for item in items
            ],
            "totalResults": int(search_info.get('totalResults', 0)),
            "searchTime": float(search_info.get('searchTime', 0)),
        }
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/collate")
async def collate_results(collate_req: CollateRequest, current_user: User = Depends(get_current_user)):
    """Collate search results AUTOMATICALLY into ALL matching categories based on protocols"""
    try:
        # Get ALL user's protocols and categories
        protocols = await db.protocols.find({"userId": current_user.id}).to_list(1000)
        categories = await db.categories.find({"userId": current_user.id}).to_list(1000)
        
        if not protocols:
            return {"success": True, "message": "No protocols found. Please create protocols first.", "categorized": 0}
        
        # Get search results
        api_key = os.environ.get('GOOGLE_API_KEY', '')
        cx = os.environ.get('GOOGLE_CX', '')
        
        if not api_key or not cx:
            raise HTTPException(status_code=500, detail="Google API credentials not configured")
        
        service = build("customsearch", "v1", developerKey=api_key)
        result = service.cse().list(
            q=collate_req.query,
            cx=cx,
            num=10
        ).execute()
        
        items = result.get('items', [])
        categorized_count = 0
        
        # For each search result, classify and AUTOMATICALLY match to ALL relevant categories
        for item in items:
            title = item.get('title', '')
            snippet = item.get('snippet', '')
            link = item.get('link', '')
            combined_text = f"{title} {snippet}".lower()
            
            # Classify content using AI
            classification = await classify_content(snippet, link)
            
            # AUTOMATICALLY match against ALL protocols
            matched_categories = []
            for protocol in protocols:
                # Parse the protocol and check if this result matches
                protocol_expression = protocol.get('booleanExpression', '').lower()
                
                # Extract all terms from protocol (simplified matching)
                # Remove special characters and get terms
                terms = re.findall(r'\(([^)]+)\)', protocol_expression)
                
                match_score = 0
                required_matches = 0
                
                for term_group in terms:
                    # Split by 'or' to get individual terms
                    or_terms = [t.strip() for t in term_group.split(' or ')]
                    required_matches += 1
                    
                    # Check if any term in this group matches
                    if any(term.lower() in combined_text for term in or_terms):
                        match_score += 1
                
                # If most terms match, add this category
                if required_matches > 0 and match_score >= (required_matches * 0.5):  # 50% match threshold
                    matched_categories.append(protocol['categoryId'])
            
            # ALWAYS save result, even if no categories matched (for user to see all results)
            search_result = {
                "userId": current_user.id,
                "title": title,
                "url": link,
                "snippet": snippet,
                "displayLink": item.get('displayLink', ''),
                "classification": classification,
                "categories": matched_categories if matched_categories else ["uncategorized"],
                "query": collate_req.query,
                "createdAt": datetime.utcnow()
            }
            
            # Check if this URL already exists for this user
            existing = await db.search_results.find_one({
                "userId": current_user.id,
                "url": link
            })
            
            if not existing:
                await db.search_results.insert_one(search_result)
                categorized_count += 1
            else:
                # Update existing result with new categories
                await db.search_results.update_one(
                    {"_id": existing["_id"]},
                    {"$set": {"categories": list(set(existing.get("categories", []) + matched_categories))}}
                )
                categorized_count += 1
        
        return {
            "success": True,
            "message": f"Successfully collated {categorized_count} results into your categories automatically!",
            "categorized": categorized_count,
            "total": len(items),
            "protocols_used": len(protocols)
        }
    except Exception as e:
        logger.error(f"Collate error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/results")
async def get_search_results(current_user: User = Depends(get_current_user), category_id: Optional[str] = None):
    """Get saved search results, optionally filtered by category"""
    query = {"userId": current_user.id}
    if category_id:
        query["categories"] = category_id
    
    results = await db.search_results.find(query).sort("createdAt", -1).limit(100).to_list(1000)
    for result in results:
        result["id"] = str(result["_id"])
        result.pop("_id")
    
    return {"success": True, "results": results}

# ==================== Subscription Routes ====================

@api_router.post("/subscription/activate")
async def activate_subscription(current_user: User = Depends(get_current_user)):
    """Activate subscription (simplified - in production integrate with Shopify)"""
    await db.users.update_one(
        {"_id": ObjectId(current_user.id)},
        {"$set": {"isPaid": True, "subscriptionStatus": "active"}}
    )
    return {"success": True, "message": "Subscription activated"}

@api_router.post("/subscription/cancel")
async def cancel_subscription(current_user: User = Depends(get_current_user)):
    """Cancel subscription"""
    await db.users.update_one(
        {"_id": ObjectId(current_user.id)},
        {"$set": {"isPaid": False, "subscriptionStatus": "cancelled"}}
    )
    return {"success": True, "message": "Subscription cancelled"}

# ==================== Admin Routes ====================

@api_router.get("/admin/users")
async def get_all_users(current_user: User = Depends(get_current_user)):
    if not current_user.isAdmin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    users = await db.users.find({}).to_list(1000)
    for user in users:
        user["id"] = str(user["_id"])
        user.pop("_id")
        user.pop("password", None)
    
    return {"success": True, "users": users}

@api_router.post("/admin/ban-user/{user_id}")
async def ban_user(user_id: str, current_user: User = Depends(get_current_user)):
    if not current_user.isAdmin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"isBanned": True}}
    )
    return {"success": True, "message": "User banned"}

# ==================== Health Check ====================

@api_router.get("/")
async def root():
    return {"message": "InfoPilot API", "version": "1.0.0", "status": "running"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

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
