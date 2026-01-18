"""
InfoPilot Explorer - PayPal Integration Routes
PayPal Orders v2 REST API integration for marketplace payments
"""

import os
import asyncio
import logging
import base64
import uuid
from datetime import datetime, timezone
from typing import Dict, Optional
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
import httpx

from utils.db import db
from utils.auth import get_current_user, require_user

router = APIRouter()
logger = logging.getLogger(__name__)

# PayPal configuration
PAYPAL_CLIENT_ID = os.environ.get("PAYPAL_CLIENT_ID")
PAYPAL_CLIENT_SECRET = os.environ.get("PAYPAL_CLIENT_SECRET")
PAYPAL_MODE = os.environ.get("PAYPAL_MODE", "sandbox")  # sandbox or live

# PayPal API URLs
PAYPAL_API_URL = "https://api-m.sandbox.paypal.com" if PAYPAL_MODE == "sandbox" else "https://api-m.paypal.com"
PAYPAL_CHECKOUT_URL = "https://www.sandbox.paypal.com" if PAYPAL_MODE == "sandbox" else "https://www.paypal.com"

# Business email for simple payments
PAYPAL_BUSINESS_EMAIL = os.environ.get("PAYPAL_BUSINESS_EMAIL", "JJspilot24@gmail.com")

# Frontend URLs
FRONTEND_URL = os.environ.get("FRONTEND_URL", "https://search-pilot.preview.emergentagent.com")


class CreateOrderRequest(BaseModel):
    protocol_id: str
    amount: float
    description: Optional[str] = None


class CaptureOrderRequest(BaseModel):
    order_id: str


async def get_paypal_access_token() -> str:
    """Get PayPal OAuth2 access token."""
    if not PAYPAL_CLIENT_ID or not PAYPAL_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="PayPal credentials not configured")
    
    auth_string = f"{PAYPAL_CLIENT_ID}:{PAYPAL_CLIENT_SECRET}"
    auth_header = base64.b64encode(auth_string.encode()).decode()
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{PAYPAL_API_URL}/v1/oauth2/token",
            headers={
                "Authorization": f"Basic {auth_header}",
                "Content-Type": "application/x-www-form-urlencoded"
            },
            data={"grant_type": "client_credentials"}
        )
        
        if response.status_code != 200:
            logger.error(f"PayPal auth failed: {response.text}")
            raise HTTPException(status_code=500, detail="PayPal authentication failed")
        
        return response.json()["access_token"]


@router.get("/config")
async def get_paypal_config():
    """Get PayPal configuration status."""
    return {
        "configured": bool(PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET),
        "mode": PAYPAL_MODE,
        "business_email": PAYPAL_BUSINESS_EMAIL,
        "client_id_preview": PAYPAL_CLIENT_ID[:10] + "..." if PAYPAL_CLIENT_ID else None,
        "simple_payments_enabled": True,  # Always enabled via direct PayPal links
        "api_url": PAYPAL_API_URL,
        "frontend_url": FRONTEND_URL
    }


@router.get("/test-payment-link")
async def get_test_payment_link():
    """Generate a test PayPal payment link to verify the business account works."""
    test_url = (
        f"https://www.paypal.com/cgi-bin/webscr?"
        f"cmd=_xclick"
        f"&business={PAYPAL_BUSINESS_EMAIL}"
        f"&item_name=InfoPilot+Test+Payment"
        f"&amount=1.00"
        f"&currency_code=USD"
        f"&return={FRONTEND_URL}/marketplace/success?test=true"
        f"&cancel_return={FRONTEND_URL}/marketplace/cancel"
    )
    
    # Alternative: PayPal.me link
    paypalme_url = "https://www.paypal.com/paypalme/JJspilot24/1"
    
    return {
        "message": "Test these links to verify your PayPal account is working",
        "standard_checkout_url": test_url,
        "paypalme_url": paypalme_url,
        "business_email": PAYPAL_BUSINESS_EMAIL,
        "instructions": [
            "1. Click one of the test links below",
            "2. If you see 'Something went wrong', your PayPal account may need configuration",
            "3. Log into PayPal.com and check for any account alerts or verification requirements",
            "4. Make sure your account can receive payments"
        ]
    }


@router.post("/create-order")
async def create_paypal_order(request: CreateOrderRequest, user: Dict = Depends(require_user)):
    """Create a PayPal order for protocol purchase."""
    
    # Get the protocol being purchased
    protocol = await db.categories.find_one(
        {"id": request.protocol_id, "is_public": True, "price": {"$gt": 0}}, 
        {"_id": 0}
    )
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found or not for sale")
    
    # Don't allow buying your own protocol
    if protocol.get("user_id") == user["id"]:
        raise HTTPException(status_code=400, detail="Cannot purchase your own protocol")
    
    # If PayPal API credentials are configured, use Orders v2 API
    if PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET:
        try:
            access_token = await get_paypal_access_token()
            
            order_payload = {
                "intent": "CAPTURE",
                "purchase_units": [{
                    "reference_id": request.protocol_id,
                    "description": f"InfoPilot Protocol: {protocol['name']}",
                    "amount": {
                        "currency_code": "USD",
                        "value": f"{request.amount:.2f}"
                    }
                }],
                "payment_source": {
                    "paypal": {
                        "experience_context": {
                            "payment_method_preference": "IMMEDIATE_PAYMENT_REQUIRED",
                            "brand_name": "InfoPilot Explorer",
                            "locale": "en-US",
                            "landing_page": "LOGIN",
                            "shipping_preference": "NO_SHIPPING",
                            "user_action": "PAY_NOW",
                            "return_url": f"{FRONTEND_URL}/marketplace/success",
                            "cancel_url": f"{FRONTEND_URL}/marketplace/cancel"
                        }
                    }
                }
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{PAYPAL_API_URL}/v2/checkout/orders",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json"
                    },
                    json=order_payload
                )
                
                if response.status_code not in [200, 201]:
                    logger.error(f"PayPal order creation failed: {response.text}")
                    raise HTTPException(status_code=500, detail="Failed to create PayPal order")
                
                order_data = response.json()
                order_id = order_data["id"]
                
                # Find the approval URL
                approval_url = None
                for link in order_data.get("links", []):
                    if link.get("rel") == "payer-action":
                        approval_url = link.get("href")
                        break
                
                # Store the pending purchase
                purchase = {
                    "id": str(uuid.uuid4()),
                    "paypal_order_id": order_id,
                    "protocol_id": request.protocol_id,
                    "buyer_id": user["id"],
                    "seller_id": protocol.get("user_id"),
                    "amount": request.amount,
                    "seller_amount": round(request.amount * 0.85, 2),  # 85% to seller
                    "platform_fee": round(request.amount * 0.15, 2),  # 15% platform fee
                    "status": "pending",
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                await db.purchases.insert_one(purchase)
                
                return {
                    "order_id": order_id,
                    "approval_url": approval_url,
                    "purchase_id": purchase["id"],
                    "status": "created"
                }
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"PayPal API error: {e}")
            # Fall back to simple payment
    
    # Fallback: Simple PayPal payment link (no API credentials needed)
    purchase_id = str(uuid.uuid4())
    
    # Use PayPal's standard checkout URL (more reliable than NCP)
    encoded_name = protocol['name'].replace(' ', '+')
    simple_url = (
        f"https://www.paypal.com/cgi-bin/webscr?"
        f"cmd=_xclick"
        f"&business={PAYPAL_BUSINESS_EMAIL}"
        f"&item_name=InfoPilot+Protocol:+{encoded_name}"
        f"&item_number={request.protocol_id}"
        f"&amount={request.amount:.2f}"
        f"&currency_code=USD"
        f"&return={FRONTEND_URL}/marketplace/success?purchase_id={purchase_id}"
        f"&cancel_return={FRONTEND_URL}/marketplace/cancel"
        f"&notify_url={FRONTEND_URL}/api/paypal/webhook"
    )
    
    # Store the pending purchase
    purchase = {
        "id": purchase_id,
        "paypal_order_id": None,
        "protocol_id": request.protocol_id,
        "buyer_id": user["id"],
        "seller_id": protocol.get("user_id"),
        "amount": request.amount,
        "seller_amount": round(request.amount * 0.85, 2),
        "platform_fee": round(request.amount * 0.15, 2),
        "status": "pending_simple",
        "payment_method": "simple_link",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.purchases.insert_one(purchase)
    
    return {
        "order_id": None,
        "approval_url": simple_url,
        "purchase_id": purchase_id,
        "status": "simple_payment",
        "message": "Using simple PayPal payment (API credentials not configured)"
    }


@router.post("/capture-order")
async def capture_paypal_order(request: CaptureOrderRequest, user: Dict = Depends(require_user)):
    """Capture a PayPal order after buyer approval."""
    
    if not PAYPAL_CLIENT_ID or not PAYPAL_CLIENT_SECRET:
        raise HTTPException(status_code=400, detail="PayPal API not configured - using simple payments")
    
    try:
        access_token = await get_paypal_access_token()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{PAYPAL_API_URL}/v2/checkout/orders/{request.order_id}/capture",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                },
                json={}
            )
            
            if response.status_code != 201:
                logger.error(f"PayPal capture failed: {response.text}")
                raise HTTPException(status_code=500, detail="Failed to capture payment")
            
            capture_data = response.json()
            
            # Update purchase status
            await db.purchases.update_one(
                {"paypal_order_id": request.order_id},
                {
                    "$set": {
                        "status": "completed",
                        "captured_at": datetime.now(timezone.utc).isoformat(),
                        "paypal_capture_id": capture_data.get("purchase_units", [{}])[0].get("payments", {}).get("captures", [{}])[0].get("id")
                    }
                }
            )
            
            # Get the purchase to update seller balance
            purchase = await db.purchases.find_one({"paypal_order_id": request.order_id}, {"_id": 0})
            if purchase and purchase.get("seller_id"):
                # Add to seller's wallet balance
                await db.users.update_one(
                    {"id": purchase["seller_id"]},
                    {"$inc": {"wallet_balance": purchase["seller_amount"]}}
                )
                
                # Record the sale
                await db.sales.insert_one({
                    "id": str(uuid.uuid4()),
                    "purchase_id": purchase["id"],
                    "seller_id": purchase["seller_id"],
                    "buyer_id": purchase["buyer_id"],
                    "protocol_id": purchase["protocol_id"],
                    "amount": purchase["amount"],
                    "seller_amount": purchase["seller_amount"],
                    "platform_fee": purchase["platform_fee"],
                    "completed_at": datetime.now(timezone.utc).isoformat()
                })
            
            return {
                "status": "captured",
                "order_id": request.order_id,
                "capture_data": capture_data
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PayPal capture error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/order/{order_id}")
async def get_order_details(order_id: str, user: Dict = Depends(require_user)):
    """Get details of a PayPal order."""
    
    if not PAYPAL_CLIENT_ID or not PAYPAL_CLIENT_SECRET:
        # Return from database for simple payments
        purchase = await db.purchases.find_one({"id": order_id}, {"_id": 0})
        if not purchase:
            raise HTTPException(status_code=404, detail="Order not found")
        return purchase
    
    try:
        access_token = await get_paypal_access_token()
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{PAYPAL_API_URL}/v2/checkout/orders/{order_id}",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=404, detail="Order not found")
            
            return response.json()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get order error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook")
async def paypal_webhook(request: Request):
    """Handle PayPal webhooks for payment notifications."""
    
    try:
        payload = await request.json()
        event_type = payload.get("event_type")
        
        logger.info(f"PayPal webhook received: {event_type}")
        
        if event_type == "PAYMENT.CAPTURE.COMPLETED":
            # Payment was captured successfully
            resource = payload.get("resource", {})
            order_id = resource.get("supplementary_data", {}).get("related_ids", {}).get("order_id")
            
            if order_id:
                await db.purchases.update_one(
                    {"paypal_order_id": order_id},
                    {"$set": {"status": "completed", "webhook_confirmed": True}}
                )
        
        elif event_type == "PAYMENT.CAPTURE.DENIED":
            # Payment was denied
            resource = payload.get("resource", {})
            order_id = resource.get("supplementary_data", {}).get("related_ids", {}).get("order_id")
            
            if order_id:
                await db.purchases.update_one(
                    {"paypal_order_id": order_id},
                    {"$set": {"status": "denied"}}
                )
        
        return {"status": "received"}
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"status": "error", "message": str(e)}


@router.get("/purchases")
async def get_my_purchases(user: Dict = Depends(require_user)):
    """Get user's purchase history."""
    purchases = await db.purchases.find(
        {"buyer_id": user["id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return {"purchases": purchases}


@router.get("/sales")
async def get_my_sales(user: Dict = Depends(require_user)):
    """Get user's sales history."""
    sales = await db.sales.find(
        {"seller_id": user["id"]},
        {"_id": 0}
    ).sort("completed_at", -1).to_list(100)
    
    return {"sales": sales, "total_earnings": sum(s.get("seller_amount", 0) for s in sales)}
