"""
InfoPilot Explorer - Stripe Payment Routes
Stripe Checkout integration for marketplace payments
"""

import os
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Optional
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from dotenv import load_dotenv

from emergentintegrations.payments.stripe.checkout import (
    StripeCheckout, 
    CheckoutSessionResponse, 
    CheckoutStatusResponse, 
    CheckoutSessionRequest
)

from utils.db import db
from utils.auth import get_current_user, require_user

# Load environment variables
load_dotenv()

router = APIRouter()
logger = logging.getLogger(__name__)

# Stripe configuration
STRIPE_API_KEY = os.environ.get("STRIPE_API_KEY", "sk_test_emergent")

# Fixed pricing packages (never accept amounts from frontend)
PROTOCOL_PACKAGES = {
    "protocol_purchase": {
        "name": "Protocol Purchase",
        "description": "Purchase a marketplace protocol"
    }
}

# Subscription packages
SUBSCRIPTION_PACKAGES = {
    "monthly": {
        "name": "InfoPilot Monthly",
        "amount": 1.00,
        "description": "Monthly subscription to InfoPilot Explorer"
    },
    "yearly": {
        "name": "InfoPilot Yearly", 
        "amount": 9.98,
        "description": "Yearly subscription to InfoPilot Explorer (save 17%!)"
    }
}


class CreateCheckoutRequest(BaseModel):
    protocol_id: Optional[str] = None
    package_type: str = "protocol_purchase"  # protocol_purchase, monthly, yearly
    origin_url: str  # Frontend origin for redirect URLs


class CheckoutStatusRequest(BaseModel):
    session_id: str


@router.get("/config")
async def get_stripe_config():
    """Get Stripe configuration status."""
    return {
        "configured": bool(STRIPE_API_KEY),
        "mode": "test" if "test" in STRIPE_API_KEY else "live",
        "subscription_packages": SUBSCRIPTION_PACKAGES,
        "features": ["one_time_payments", "subscriptions", "marketplace"]
    }


@router.post("/create-checkout")
async def create_stripe_checkout(
    request: CreateCheckoutRequest, 
    http_request: Request,
    user: Dict = Depends(require_user)
):
    """Create a Stripe checkout session for protocol purchase or subscription."""
    
    # Determine amount and metadata based on package type
    if request.package_type in ["monthly", "yearly"]:
        # Subscription purchase
        package = SUBSCRIPTION_PACKAGES.get(request.package_type)
        if not package:
            raise HTTPException(status_code=400, detail="Invalid subscription package")
        
        amount = package["amount"]
        item_name = package["name"]
        metadata = {
            "type": "subscription",
            "package": request.package_type,
            "user_id": user["id"],
            "user_email": user.get("email", "")
        }
        
    elif request.package_type == "protocol_purchase" and request.protocol_id:
        # Protocol purchase from marketplace
        protocol = await db.categories.find_one(
            {"id": request.protocol_id, "is_public": True, "price": {"$gt": 0}},
            {"_id": 0}
        )
        if not protocol:
            raise HTTPException(status_code=404, detail="Protocol not found or not for sale")
        
        if protocol.get("user_id") == user["id"]:
            raise HTTPException(status_code=400, detail="Cannot purchase your own protocol")
        
        # Get amount from database (NEVER from frontend)
        amount = float(protocol.get("price", 0))
        if amount <= 0:
            raise HTTPException(status_code=400, detail="Invalid protocol price")
        
        item_name = f"InfoPilot Protocol: {protocol['name']}"
        metadata = {
            "type": "protocol_purchase",
            "protocol_id": request.protocol_id,
            "protocol_name": protocol["name"],
            "seller_id": protocol.get("user_id", ""),
            "buyer_id": user["id"],
            "buyer_email": user.get("email", ""),
            "seller_amount": str(round(amount * 0.85, 2)),  # 85% to seller
            "platform_fee": str(round(amount * 0.15, 2))   # 15% platform fee
        }
    else:
        raise HTTPException(status_code=400, detail="Invalid package type or missing protocol_id")
    
    # Build dynamic success/cancel URLs from frontend origin
    success_url = f"{request.origin_url}/payment/success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{request.origin_url}/payment/cancel"
    
    # Initialize Stripe checkout
    host_url = str(http_request.base_url)
    webhook_url = f"{host_url}api/stripe/webhook"
    
    try:
        stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
        
        # Create checkout session request
        checkout_request = CheckoutSessionRequest(
            amount=amount,
            currency="usd",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata=metadata
        )
        
        # Create checkout session
        session: CheckoutSessionResponse = await stripe_checkout.create_checkout_session(checkout_request)
        
        # Create payment transaction record BEFORE redirect
        transaction = {
            "id": str(uuid.uuid4()),
            "session_id": session.session_id,
            "user_id": user["id"],
            "user_email": user.get("email", ""),
            "amount": amount,
            "currency": "usd",
            "item_name": item_name,
            "metadata": metadata,
            "payment_status": "pending",
            "status": "initiated",
            "provider": "stripe",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.payment_transactions.insert_one(transaction)
        
        logger.info(f"Stripe checkout session created: {session.session_id} for user {user['id']}")
        
        return {
            "checkout_url": session.url,
            "session_id": session.session_id,
            "amount": amount,
            "currency": "usd"
        }
        
    except Exception as e:
        logger.error(f"Stripe checkout creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create checkout session: {str(e)}")


@router.get("/status/{session_id}")
async def get_checkout_status(session_id: str, user: Dict = Depends(require_user)):
    """Get the status of a Stripe checkout session and update database."""
    
    # First check if we already processed this payment
    existing_transaction = await db.payment_transactions.find_one(
        {"session_id": session_id},
        {"_id": 0}
    )
    
    if not existing_transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # If already completed, return cached status
    if existing_transaction.get("payment_status") == "paid":
        return {
            "status": existing_transaction.get("status"),
            "payment_status": existing_transaction.get("payment_status"),
            "amount": existing_transaction.get("amount"),
            "currency": existing_transaction.get("currency"),
            "already_processed": True
        }
    
    try:
        stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url="")
        
        # Get status from Stripe
        status_response: CheckoutStatusResponse = await stripe_checkout.get_checkout_status(session_id)
        
        # Update transaction in database
        update_data = {
            "status": status_response.status,
            "payment_status": status_response.payment_status,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        # If payment completed, process the purchase
        if status_response.payment_status == "paid" and existing_transaction.get("payment_status") != "paid":
            update_data["completed_at"] = datetime.now(timezone.utc).isoformat()
            
            metadata = existing_transaction.get("metadata", {})
            
            # Handle protocol purchase completion
            if metadata.get("type") == "protocol_purchase":
                seller_id = metadata.get("seller_id")
                seller_amount = float(metadata.get("seller_amount", 0))
                
                if seller_id and seller_amount > 0:
                    # Add to seller's wallet balance
                    await db.users.update_one(
                        {"id": seller_id},
                        {"$inc": {"wallet_balance": seller_amount}}
                    )
                    
                    # Record the sale
                    await db.sales.insert_one({
                        "id": str(uuid.uuid4()),
                        "transaction_id": existing_transaction["id"],
                        "session_id": session_id,
                        "seller_id": seller_id,
                        "buyer_id": metadata.get("buyer_id"),
                        "protocol_id": metadata.get("protocol_id"),
                        "amount": existing_transaction.get("amount"),
                        "seller_amount": seller_amount,
                        "platform_fee": float(metadata.get("platform_fee", 0)),
                        "provider": "stripe",
                        "completed_at": datetime.now(timezone.utc).isoformat()
                    })
                    
                    logger.info(f"Protocol sale completed: {metadata.get('protocol_id')} to {metadata.get('buyer_id')}")
            
            # Handle subscription completion
            elif metadata.get("type") == "subscription":
                # Update user's subscription status
                await db.users.update_one(
                    {"id": existing_transaction["user_id"]},
                    {
                        "$set": {
                            "subscription_active": True,
                            "subscription_type": metadata.get("package"),
                            "subscription_started_at": datetime.now(timezone.utc).isoformat()
                        }
                    }
                )
                logger.info(f"Subscription activated for user {existing_transaction['user_id']}")
        
        # Update the transaction record
        await db.payment_transactions.update_one(
            {"session_id": session_id},
            {"$set": update_data}
        )
        
        return {
            "status": status_response.status,
            "payment_status": status_response.payment_status,
            "amount": status_response.amount_total / 100,  # Convert from cents
            "currency": status_response.currency,
            "already_processed": False
        }
        
    except Exception as e:
        logger.error(f"Error getting checkout status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get checkout status: {str(e)}")


@router.post("/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks for payment notifications."""
    
    try:
        body = await request.body()
        signature = request.headers.get("Stripe-Signature", "")
        
        stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url="")
        webhook_response = await stripe_checkout.handle_webhook(body, signature)
        
        logger.info(f"Stripe webhook received: {webhook_response.event_type}")
        
        # Update transaction based on webhook event
        if webhook_response.session_id:
            await db.payment_transactions.update_one(
                {"session_id": webhook_response.session_id},
                {
                    "$set": {
                        "payment_status": webhook_response.payment_status,
                        "webhook_event": webhook_response.event_type,
                        "webhook_received_at": datetime.now(timezone.utc).isoformat()
                    }
                }
            )
        
        return {"status": "received", "event_type": webhook_response.event_type}
        
    except Exception as e:
        logger.error(f"Stripe webhook error: {str(e)}")
        return {"status": "error", "message": str(e)}


@router.get("/transactions")
async def get_my_transactions(user: Dict = Depends(require_user)):
    """Get user's payment transaction history."""
    
    transactions = await db.payment_transactions.find(
        {"user_id": user["id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return {"transactions": transactions}
