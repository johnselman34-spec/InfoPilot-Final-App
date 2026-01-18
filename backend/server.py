from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="InfoPilot Explorer API", description="API for Letters to Evelyn & Maestro Bistro")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# ============ MODELS ============

# Status Check Models
class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str

# Newsletter Signup Model
class NewsletterSignup(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    name: str
    signup_type: str = "general"  # general, book, foodtruck
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class NewsletterSignupCreate(BaseModel):
    email: EmailStr
    name: str
    signup_type: str = "general"

# Book Order Model
class BookOrder(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_name: str
    email: EmailStr
    book_format: str  # ebook, paperback, hardcover
    quantity: int = 1
    total_price: float
    status: str = "pending"  # pending, confirmed, shipped
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class BookOrderCreate(BaseModel):
    customer_name: str
    email: EmailStr
    book_format: str
    quantity: int = 1

# Food Order Model
class FoodOrderItem(BaseModel):
    item_name: str
    quantity: int
    price: float
    special_instructions: Optional[str] = None

class FoodOrder(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_name: str
    phone: str
    email: Optional[EmailStr] = None
    items: List[FoodOrderItem]
    total_price: float
    pickup_time: str
    status: str = "pending"  # pending, preparing, ready, completed
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class FoodOrderCreate(BaseModel):
    customer_name: str
    phone: str
    email: Optional[EmailStr] = None
    items: List[FoodOrderItem]
    pickup_time: str

# Contact Message Model
class ContactMessage(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: EmailStr
    subject: str
    message: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ContactMessageCreate(BaseModel):
    name: str
    email: EmailStr
    subject: str
    message: str

# Testimonial Model
class Testimonial(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    location: str
    rating: int
    review: str
    review_type: str  # book, food
    featured: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ============ BOOK PRICING ============
BOOK_PRICES = {
    "ebook": 4.99,
    "paperback": 17.90,
    "hardcover": 24.99
}

# ============ INFOPILOT SUBSCRIPTION ============
INFOPILOT_PLANS = {
    "monthly": {
        "price": 1.00,
        "description": "InfoPilot Explorer Monthly - Boolean search and categorization for scholars and tradesmen",
        "features": ["Unlimited searches", "Category organization", "Collaboration tools", "Priority support"]
    },
    "yearly": {
        "price": 9.98,
        "description": "InfoPilot Explorer Yearly - Save 17%!",
        "features": ["All monthly features", "Advanced analytics", "Custom categories", "API access"]
    }
}

# ============ FOOD MENU ============
FOOD_MENU = [
    {
        "id": "beef-rouladen",
        "name": "German Beef Rouladen",
        "description": "deLectaBLe thin slices of tender beef rolled around pickles, onions, and mustard, slow-braised in rich gravy. Served with red cabbage and spätzle. Warning: May cause involuntary 'Wunderbar!' exclamations!",
        "price": 18.99,
        "category": "main",
        "image": "🥩",
        "funny_tagline": "So luscious and tender, your grandmother in Germany will call to apologize!"
    },
    {
        "id": "veggie-rouladen",
        "name": "Vegetable Rouladen",
        "description": "Magnificent rolled vegetables stuffed with savory goodness, perfectly spiced and braised to perfection. Even carnivores will consider switching sides!",
        "price": 15.99,
        "category": "main",
        "image": "🥬",
        "funny_tagline": "Plants have feelings too – delicious ones!"
    },
    {
        "id": "fish-chowder",
        "name": "Perfectly Spiced Fish Chowder",
        "description": "Fresh Atlantic fish swimming in a creamy, perfectly spiced chowder straight from the Maine coast. Served with crusty bread. Warning: May cause spontaneous sea shanty singing!",
        "price": 14.99,
        "category": "soup",
        "image": "🐟",
        "funny_tagline": "The only fish story that is 100% true and delicious!"
    },
    {
        "id": "pretzel",
        "name": "Giant Bavarian Pretzel",
        "description": "Freshly baked twisted beauty served with beer cheese and mustard. Warning: Size may cause jaw unhinging!",
        "price": 8.99,
        "category": "appetizer",
        "image": "🥨",
        "funny_tagline": "Twisted like our sense of humor!"
    },
    {
        "id": "apple-strudel",
        "name": "Oma's Apple Strudel",
        "description": "Grandma's secret recipe with crispy phyllo, tender apples, and cinnamon. Served warm with vanilla sauce. May induce nostalgic tears!",
        "price": 7.99,
        "category": "dessert",
        "image": "🥧",
        "funny_tagline": "Warning: Grandmother not included!"
    }
]

# ============ COMPANY INFO ============
COMPANY_INFO = {
    "corporation": "Top Pilot Enterprises, Inc.",
    "founded": "2025",
    "subsidiaries": [
        {
            "name": "InfoPilot Explorer, LLC",
            "description": "Mobile and desktop application solution for information exchange between scholars and tradesmen using boolean search and categorization"
        },
        {
            "name": "Maestro Bistro",
            "description": "Food truck serving delectable German cuisine on the Mall in Brunswick, Maine"
        },
        {
            "name": "John Selman Publications",
            "description": "Publishing arm featuring Letters to Evelyn - a True Supernatural Thriller Comedy"
        }
    ],
    "tagline": "Where Every Flight Leads to Flavor and Every Page Leads to Laughter!"
}

# ============ BOOK INFO ============
BOOK_INFO = {
    "title": "Letters to Evelyn",
    "author": "John Selman",
    "publisher": "John Selman Publications (A Top Pilot Enterprises, Inc. Company)",
    "genre": "True Supernatural Thriller Comedy",
    "description": "A True unbelievable Story! A True even more unforgettable Story! Man saves Universe with his Memoir!",
    "long_description": "Letters to Evelyn is a hysterically heartwarming journey on a hilarious roller coaster ride to the unwitting heavens! This Naval Aviation autobiography is just the ticket to profusely jocose 'entertainment value' involved with a flight student's hysterical quest, averting jealous murder attempts from his stepmother, to find his one true soulmate. With 70 finely-crafted, deafening, zany, zesty zoo zingers causing hurricane-force winds of laughter from the most skeptical of minds!",
    "isbn_ebook": "979-8-9985974-4-2",
    "isbn_paperback": "979-8-9985974-8-0",
    "isbn_hardcover": "979-8-9985974-9-7",
    "copyright": "© 2014 John Selman",
    "amazon_link": "https://www.amazon.com/dp/B0CTJM7HXG",
    "google_play_link": "https://play.google.com/store/books",
    "reedsy_link": "https://reedsy.com",
    "review_count": 19,
    "review_source": "Readers' Favorite - 5 Star Reviews",
    "film_news": "Recently accepted by Voyage Media producer Ryan Heppe for production into a film. Heppe previously worked with Arnold Schwarzenegger and Bruce Willis!",
    "warnings": [
        "Not intended for use while operating a vehicle or heavy equipment - may cause distraction!",
        "Pregnant or breastfeeding individuals should avoid due to potential for 'uncontrollable hysterics and fits of laughter'",
        "Intended for adults only (26 years and older)",
        "Author is not responsible for health problems or damages associated with humor or profound material",
        "Contains 70+ jokes that may cause hurricane-force winds of laughter!"
    ],
    "chapters": [
        "Eve",
        "Dear Evelyn",
        "Introduction",
        "The Selman Chronicles: Pilot",
        "The Encounter",
        "New Year's 2000",
        "Muster the Strength",
        "Respectful to my father",
        "Unfriendly Demeanor",
        "The Sweltering, Sizzling and Sultry Speech",
        "Grandmother Selman",
        "Flight School Time",
        "Foraging for Air",
        "USS Nimitz and the Heavens Above",
        "The Horrors of War and the Buildup to the Prophesies",
        "...and 10 more thrilling chapters including Chapter 25: Caught in the Act of Elsewhere!"
    ],
    "author_bio": {
        "name": "John Jackson Selman III",
        "birthplace": "Albuquerque, New Mexico",
        "hometown": "Brunswick, Maine",
        "education": "Graduated first in NROTC at the University of Maine with a B.A. in German",
        "service": "U.S. Navy Pilot and Division Officer",
        "aircraft_flown": "10 different types of aircraft",
        "world_records": [
            "Longest time spent without sleep - more than 12 days",
            "Steepest, highest Sarajevo Approach with lowest recovery in a T-34C"
        ],
        "family_legacy": "Grandfather was Deputy JAG of the U.S. Navy and an Admiral"
    },
    "professional_reviews": [
        {
            "quote": "Letters to Evelyn by John Selman is an extraordinary book with a unique plot that captivated me from the first chapter. The author takes quite horrific and disturbing events and turns them into great learning experiences. Each of the characters, even the minor ones, has been portrayed with care and consideration. Letters to Evelyn will never lose your interest and never fail to deliver on tension, excitement and even hints of comedy.",
            "author": "L. Jones",
            "source": "Readers' Favorite - 5 Stars"
        },
        {
            "quote": "The comical side of it is exceedingly brilliant, to the point that even when I wasn't busy reading, the story would creep into my mind, and I would start laughing abruptly. John's quirky style of writing, his truthfulness in his thoughts, and the unusual events in Letters to Evelyn make for an interesting and very unique book.",
            "author": "Professional Reviewer",
            "source": "Readers' Favorite - 5 Stars"
        },
        {
            "quote": "John Selman delivers one of the most remarkable works I have ever read... The visuals are beautiful, from the eye-catching cover to the elegant fonts and consistent format. I thoroughly enjoyed reading this book and highly recommend it to anyone seeking a truly delightful and lovable reading experience.",
            "author": "Professional Reviewer",
            "source": "Readers' Favorite - 5 Stars"
        },
        {
            "quote": "The tour along the Intergalactic Superhighway to Neptune was one of the best stories I have recently read! I highly recommend this unique read to adult fans of memoirs, science fiction, and fantasy.",
            "author": "Professional Reviewer",
            "source": "Readers' Favorite - 5 Stars"
        },
        {
            "quote": "This is a profound and unforgettable literary piece. Mind-bending. Exceedingly brilliant. The author's imagination is off the charts. Mind-blowing.",
            "author": "Professional Reviewer",
            "source": "Readers' Favorite - 5 Stars"
        }
    ]
}

# ============ ROUTES ============

@api_router.get("/")
async def root():
    return {
        "message": "Welcome to InfoPilot Explorer API!",
        "app_name": "InfoPilot Explorer",
        "tagline": "Where Books Meet Beef Rouladen and Reality Gets Weird!",
        "version": "1.0.0"
    }

# Status Routes
@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.model_dump()
    status_obj = StatusCheck(**status_dict)
    doc = status_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    _ = await db.status_checks.insert_one(doc)
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
    for check in status_checks:
        if isinstance(check['timestamp'], str):
            check['timestamp'] = datetime.fromisoformat(check['timestamp'])
    return status_checks

# Book Info Routes
@api_router.get("/book")
async def get_book_info():
    return BOOK_INFO

@api_router.get("/book/prices")
async def get_book_prices():
    return BOOK_PRICES

# Company Info Routes
@api_router.get("/company")
async def get_company_info():
    return COMPANY_INFO

# InfoPilot Subscription Routes
@api_router.get("/infopilot/plans")
async def get_infopilot_plans():
    return INFOPILOT_PLANS

# Book Order Routes
@api_router.post("/book/order", response_model=BookOrder)
async def create_book_order(order: BookOrderCreate):
    if order.book_format not in BOOK_PRICES:
        raise HTTPException(status_code=400, detail="Invalid book format")
    
    total_price = BOOK_PRICES[order.book_format] * order.quantity
    
    book_order = BookOrder(
        customer_name=order.customer_name,
        email=order.email,
        book_format=order.book_format,
        quantity=order.quantity,
        total_price=total_price
    )
    
    doc = book_order.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.book_orders.insert_one(doc)
    
    return book_order

@api_router.get("/book/orders", response_model=List[BookOrder])
async def get_book_orders():
    orders = await db.book_orders.find({}, {"_id": 0}).to_list(1000)
    for order in orders:
        if isinstance(order['created_at'], str):
            order['created_at'] = datetime.fromisoformat(order['created_at'])
    return orders

# Food Menu Routes
@api_router.get("/food/menu")
async def get_food_menu():
    return {
        "restaurant_name": "Maestro Bistro",
        "parent_company": "Top Pilot Enterprises, Inc.",
        "tagline": "Where Every Bite is a Symphony of Flavor!",
        "location": "The Mall, Brunswick, Maine",
        "description": "Your friendly neighborhood food truck serving up deLectaBLe German delicacies with a side of laughs! Part of Top Pilot Enterprises, Inc.",
        "menu": FOOD_MENU
    }

@api_router.get("/food/menu/{item_id}")
async def get_menu_item(item_id: str):
    for item in FOOD_MENU:
        if item["id"] == item_id:
            return item
    raise HTTPException(status_code=404, detail="Menu item not found")

# Food Order Routes
@api_router.post("/food/order", response_model=FoodOrder)
async def create_food_order(order: FoodOrderCreate):
    total_price = 0.0
    for item in order.items:
        menu_item = next((m for m in FOOD_MENU if m["name"] == item.item_name), None)
        if menu_item:
            total_price += menu_item["price"] * item.quantity
        else:
            total_price += item.price * item.quantity
    
    food_order = FoodOrder(
        customer_name=order.customer_name,
        phone=order.phone,
        email=order.email,
        items=[item.model_dump() for item in order.items],
        total_price=total_price,
        pickup_time=order.pickup_time
    )
    
    doc = food_order.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.food_orders.insert_one(doc)
    
    return food_order

@api_router.get("/food/orders", response_model=List[FoodOrder])
async def get_food_orders():
    orders = await db.food_orders.find({}, {"_id": 0}).to_list(1000)
    for order in orders:
        if isinstance(order['created_at'], str):
            order['created_at'] = datetime.fromisoformat(order['created_at'])
    return orders

# Newsletter Routes
@api_router.post("/newsletter/signup", response_model=NewsletterSignup)
async def newsletter_signup(signup: NewsletterSignupCreate):
    # Check if email already exists
    existing = await db.newsletter_signups.find_one({"email": signup.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already subscribed! You're already part of the fun!")
    
    newsletter = NewsletterSignup(**signup.model_dump())
    doc = newsletter.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.newsletter_signups.insert_one(doc)
    
    return newsletter

@api_router.get("/newsletter/subscribers")
async def get_newsletter_subscribers():
    subscribers = await db.newsletter_signups.find({}, {"_id": 0}).to_list(1000)
    return {"total": len(subscribers), "subscribers": subscribers}

# Contact Routes
@api_router.post("/contact", response_model=ContactMessage)
async def create_contact_message(message: ContactMessageCreate):
    contact = ContactMessage(**message.model_dump())
    doc = contact.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.contact_messages.insert_one(doc)
    return contact

@api_router.get("/contact/messages", response_model=List[ContactMessage])
async def get_contact_messages():
    messages = await db.contact_messages.find({}, {"_id": 0}).to_list(1000)
    for msg in messages:
        if isinstance(msg['created_at'], str):
            msg['created_at'] = datetime.fromisoformat(msg['created_at'])
    return messages

# Testimonials Routes
@api_router.get("/testimonials")
async def get_testimonials():
    # Professional reviews from Readers' Favorite
    professional_reviews = [
        {
            "id": str(uuid.uuid4()),
            "name": "L. Jones",
            "location": "Readers' Favorite",
            "rating": 5,
            "review": "Letters to Evelyn by John Selman is an extraordinary book with a unique plot that captivated me from the first chapter. The author takes quite horrific and disturbing events and turns them into great learning experiences. Letters to Evelyn will never lose your interest and never fail to deliver on tension, excitement and even hints of comedy.",
            "review_type": "book",
            "featured": True,
            "source": "Readers' Favorite - 5 Star Professional Review"
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Professional Reviewer",
            "location": "Readers' Favorite",
            "rating": 5,
            "review": "The comical side of it is exceedingly brilliant, to the point that even when I wasn't busy reading, the story would creep into my mind, and I would start laughing abruptly. John's quirky style of writing, his truthfulness in his thoughts, and the unusual events make for an interesting and very unique book.",
            "review_type": "book",
            "featured": True,
            "source": "Readers' Favorite - 5 Star Professional Review"
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Book Critic",
            "location": "Readers' Favorite",
            "rating": 5,
            "review": "John Selman delivers one of the most remarkable works I have ever read... The visuals are beautiful, from the eye-catching cover to the elegant fonts and consistent format. I thoroughly enjoyed reading this book and highly recommend it to anyone seeking a truly delightful and lovable reading experience.",
            "review_type": "book",
            "featured": True,
            "source": "Readers' Favorite - 5 Star Professional Review"
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Literary Reviewer",
            "location": "Readers' Favorite",
            "rating": 5,
            "review": "The tour along the Intergalactic Superhighway to Neptune was one of the best stories I have recently read! I highly recommend this unique read to adult fans of memoirs, science fiction, and fantasy. Mind-bending. Exceedingly brilliant. The author's imagination is off the charts. Mind-blowing.",
            "review_type": "book",
            "featured": True,
            "source": "Readers' Favorite - 5 Star Professional Review"
        },
    ]
    
    # Fun testimonials
    default_testimonials = [
        {
            "id": str(uuid.uuid4()),
            "name": "Captain Crunch",
            "location": "The High Seas",
            "rating": 5,
            "review": "I've sailed the seven seas and read 'Letters to Evelyn' on every single one. My crew now thinks I'm crazy. Worth it!",
            "review_type": "book",
            "featured": True
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Hans the Hungry",
            "location": "Brunswick, ME",
            "rating": 5,
            "review": "The beef rouladen at Maestro Bistro made me call my grandmother in Germany to apologize. It's THAT good! So luscious and tender!",
            "review_type": "food",
            "featured": True
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Area 51 Employee",
            "location": "[REDACTED]",
            "rating": 5,
            "review": "Finally, a book that gets the alien stuff right! I mean... what aliens? *nervous laughter*",
            "review_type": "book",
            "featured": True
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Chowder Charlie",
            "location": "Maine Coast",
            "rating": 5,
            "review": "The fish chowder made me emotional. My lobster pot is jealous. My wife is understanding. 11/10!",
            "review_type": "food",
            "featured": True
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Former Skeptic Steve",
            "location": "Everywhere and Nowhere",
            "rating": 5,
            "review": "I used to not believe in anything. Now I believe in this book AND German food trucks. Life changed! 70 jokes that caused hurricane-force laughter!",
            "review_type": "book",
            "featured": True
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Veggie Victor",
            "location": "Portland, ME",
            "rating": 5,
            "review": "The Vegetable Rouladen converted three meat-eaters in my family. They're still confused but deliciously happy!",
            "review_type": "food",
            "featured": True
        }
    ]
    
    # Get any user-submitted testimonials from DB
    db_testimonials = await db.testimonials.find({}, {"_id": 0}).to_list(100)
    
    return {"testimonials": professional_reviews + default_testimonials + db_testimonials}

# Stats for Dashboard
@api_router.get("/stats")
async def get_stats():
    book_orders = await db.book_orders.count_documents({})
    food_orders = await db.food_orders.count_documents({})
    subscribers = await db.newsletter_signups.count_documents({})
    messages = await db.contact_messages.count_documents({})
    
    return {
        "book_orders": book_orders,
        "food_orders": food_orders,
        "newsletter_subscribers": subscribers,
        "contact_messages": messages,
        "fun_fact": "You're awesome for checking stats!"
    }

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
