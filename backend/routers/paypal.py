"""
PayPal Router - InfoPilot Explorer
Handles PayPal payment integration for subscriptions and marketplace purchases
"""

from fastapi import APIRouter, HTTPException, Request
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
from datetime import datetime, timezone
import os
import uuid
import httpx
import base64
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/paypal", tags=["PayPal"])

# Database connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'infopilot_explorer')]

# PayPal Configuration
PAYPAL_CLIENT_ID = os.environ.get('PAYPAL_CLIENT_ID', '')
PAYPAL_SECRET = os.environ.get('PAYPAL_SECRET', '')
PAYPAL_API_BASE = os.environ.get('PAYPAL_API_BASE', 'https://api-m.sandbox.paypal.com')

# Default PayPal email for receiving payments
PAYPAL_RECIPIENT_EMAIL = "JJspilot24@gmail.com"


async def get_paypal_access_token() -> str:
    """Get PayPal OAuth access token"""
    if not PAYPAL_CLIENT_ID or not PAYPAL_SECRET:
        logger.warning("PayPal credentials not configured")
        return ""
    
    auth = base64.b64encode(f"{PAYPAL_CLIENT_ID}:{PAYPAL_SECRET}".encode()).decode()
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{PAYPAL_API_BASE}/v1/oauth2/token",
            headers={
                "Authorization": f"Basic {auth}",
                "Content-Type": "application/x-www-form-urlencoded"
            },
            data="grant_type=client_credentials"
        )
        
        if response.status_code == 200:
            return response.json().get("access_token", "")
        else:
            logger.error(f"PayPal auth failed: {response.text}")
            return ""


@router.post("/create-order")
async def create_paypal_order(request: Request):
    """Create a PayPal order for checkout"""
    data = await request.json()
    
    amount = data.get("amount", 0)
    currency = data.get("currency", "USD")
    description = data.get("description", "InfoPilot Explorer Purchase")
    item_type = data.get("item_type", "subscription")  # subscription, protocol, book
    item_id = data.get("item_id")
    user_id = data.get("user_id")
    
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid amount")
    
    # Get PayPal access token
    access_token = await get_paypal_access_token()
    
    if not access_token:
        # Fallback: Create a manual payment record and return PayPal.me link
        order_id = str(uuid.uuid4())
        await db.paypal_orders.insert_one({
            "order_id": order_id,
            "user_id": user_id,
            "amount": amount,
            "currency": currency,
            "description": description,
            "item_type": item_type,
            "item_id": item_id,
            "status": "CREATED",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "paypal_method": "manual"
        })
        
        return {
            "order_id": order_id,
            "status": "manual_payment",
            "paypal_link": f"https://www.paypal.com/paypalme/infopilot/{amount}",
            "paypal_email": PAYPAL_RECIPIENT_EMAIL,
            "message": "Please send payment and include order ID in notes"
        }
    
    # Create PayPal order via API
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{PAYPAL_API_BASE}/v2/checkout/orders",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            },
            json={
                "intent": "CAPTURE",
                "purchase_units": [{
                    "reference_id": item_id or str(uuid.uuid4()),
                    "description": description,
                    "amount": {
                        "currency_code": currency,
                        "value": f"{amount:.2f}"
                    }
                }],
                "application_context": {
                    "brand_name": "InfoPilot Explorer",
                    "landing_page": "NO_PREFERENCE",
                    "user_action": "PAY_NOW",
                    "return_url": f"{os.environ.get('FRONTEND_URL', '')}/payment-success?provider=paypal",
                    "cancel_url": f"{os.environ.get('FRONTEND_URL', '')}/payment-cancelled"
                }
            }
        )
        
        if response.status_code in [200, 201]:
            paypal_order = response.json()
            
            # Store order in database
            await db.paypal_orders.insert_one({
                "order_id": paypal_order["id"],
                "user_id": user_id,
                "amount": amount,
                "currency": currency,
                "description": description,
                "item_type": item_type,
                "item_id": item_id,
                "status": paypal_order["status"],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "paypal_method": "api"
            })
            
            # Find approval URL
            approval_url = next(
                (link["href"] for link in paypal_order.get("links", []) 
                 if link.get("rel") == "approve"),
                None
            )
            
            return {
                "order_id": paypal_order["id"],
                "status": paypal_order["status"],
                "approval_url": approval_url
            }
        else:
            logger.error(f"PayPal order creation failed: {response.text}")
            raise HTTPException(status_code=500, detail="Failed to create PayPal order")


@router.post("/capture-order/{order_id}")
async def capture_paypal_order(order_id: str, request: Request):
    """Capture (complete) a PayPal order after user approval"""
    access_token = await get_paypal_access_token()
    
    if not access_token:
        raise HTTPException(status_code=503, detail="PayPal service unavailable")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{PAYPAL_API_BASE}/v2/checkout/orders/{order_id}/capture",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
        )
        
        if response.status_code in [200, 201]:
            capture_result = response.json()
            
            # Update order in database
            await db.paypal_orders.update_one(
                {"order_id": order_id},
                {"$set": {
                    "status": capture_result["status"],
                    "captured_at": datetime.now(timezone.utc).isoformat(),
                    "capture_details": capture_result
                }}
            )
            
            # If payment successful, fulfill the order
            if capture_result["status"] == "COMPLETED":
                order = await db.paypal_orders.find_one({"order_id": order_id})
                if order:
                    await fulfill_order(order)
            
            return {
                "order_id": order_id,
                "status": capture_result["status"],
                "message": "Payment captured successfully" if capture_result["status"] == "COMPLETED" else "Payment processing"
            }
        else:
            logger.error(f"PayPal capture failed: {response.text}")
            raise HTTPException(status_code=500, detail="Failed to capture payment")


@router.get("/order-status/{order_id}")
async def get_order_status(order_id: str):
    """Get the status of a PayPal order"""
    order = await db.paypal_orders.find_one(
        {"order_id": order_id},
        {"_id": 0}
    )
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return order


@router.post("/webhook")
async def paypal_webhook(request: Request):
    """Handle PayPal webhook events"""
    data = await request.json()
    event_type = data.get("event_type", "")
    
    logger.info(f"PayPal webhook received: {event_type}")
    
    # Store webhook event
    await db.paypal_webhooks.insert_one({
        "event_id": data.get("id"),
        "event_type": event_type,
        "data": data,
        "received_at": datetime.now(timezone.utc).isoformat()
    })
    
    # Process different event types
    if event_type == "CHECKOUT.ORDER.APPROVED":
        order_id = data.get("resource", {}).get("id")
        if order_id:
            # Auto-capture the payment
            await capture_paypal_order(order_id, request)
    
    elif event_type == "PAYMENT.CAPTURE.COMPLETED":
        resource = data.get("resource", {})
        order_id = resource.get("supplementary_data", {}).get("related_ids", {}).get("order_id")
        if order_id:
            await db.paypal_orders.update_one(
                {"order_id": order_id},
                {"$set": {"status": "COMPLETED", "webhook_confirmed": True}}
            )
    
    elif event_type == "PAYMENT.CAPTURE.DENIED":
        resource = data.get("resource", {})
        order_id = resource.get("supplementary_data", {}).get("related_ids", {}).get("order_id")
        if order_id:
            await db.paypal_orders.update_one(
                {"order_id": order_id},
                {"$set": {"status": "DENIED"}}
            )
    
    return {"status": "received"}


async def fulfill_order(order: dict):
    """Fulfill an order based on item type"""
    item_type = order.get("item_type")
    item_id = order.get("item_id")
    user_id = order.get("user_id")
    
    if item_type == "subscription":
        # Activate subscription
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {
                "subscription_active": True,
                "subscription_started": datetime.now(timezone.utc).isoformat(),
                "subscription_amount_paid": order.get("amount")
            }}
        )
    
    elif item_type == "protocol":
        # Grant protocol access
        await db.user_protocols.insert_one({
            "user_id": user_id,
            "protocol_id": item_id,
            "purchased_at": datetime.now(timezone.utc).isoformat(),
            "amount_paid": order.get("amount")
        })
    
    elif item_type == "book":
        # Grant book access (Letters to Evelyn)
        await db.user_purchases.insert_one({
            "user_id": user_id,
            "item_type": "book",
            "item_id": item_id,
            "purchased_at": datetime.now(timezone.utc).isoformat(),
            "amount_paid": order.get("amount")
        })
    
    # Record payment
    await db.payments.insert_one({
        "payment_id": str(uuid.uuid4()),
        "user_id": user_id,
        "provider": "paypal",
        "order_id": order.get("order_id"),
        "amount": order.get("amount"),
        "currency": order.get("currency", "USD"),
        "item_type": item_type,
        "item_id": item_id,
        "status": "completed",
        "created_at": datetime.now(timezone.utc).isoformat()
    })


@router.get("/config")
async def get_paypal_config():
    """Get PayPal client configuration for frontend"""
    return {
        "client_id": PAYPAL_CLIENT_ID if PAYPAL_CLIENT_ID else None,
        "paypal_email": PAYPAL_RECIPIENT_EMAIL,
        "is_configured": bool(PAYPAL_CLIENT_ID and PAYPAL_SECRET),
        "mode": "sandbox" if "sandbox" in PAYPAL_API_BASE else "live"
    }
