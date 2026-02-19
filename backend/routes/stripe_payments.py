"""
Stripe Payment Integration for InfoPilot Explorer
Handles payment processing for premium features and protocol purchases
"""
import os
import stripe
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone

# Initialize Stripe
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY', '')

router = APIRouter(prefix="/api/stripe", tags=["stripe"])

# Models
class CreateCheckoutSession(BaseModel):
    price_id: Optional[str] = None
    amount: Optional[int] = None  # Amount in cents
    product_name: str = "InfoPilot Premium"
    success_url: str
    cancel_url: str
    metadata: Optional[dict] = None

class CreatePaymentIntent(BaseModel):
    amount: int  # Amount in cents
    currency: str = "usd"
    description: Optional[str] = None
    metadata: Optional[dict] = None

class WebhookEvent(BaseModel):
    type: str
    data: dict

# Endpoints
@router.get("/config")
async def get_stripe_config():
    """Get Stripe publishable key for frontend"""
    publishable_key = os.environ.get('STRIPE_PUBLISHABLE_KEY', '')
    return {
        "publishable_key": publishable_key,
        "enabled": bool(publishable_key and stripe.api_key)
    }

@router.post("/create-checkout-session")
async def create_checkout_session(data: CreateCheckoutSession):
    """Create a Stripe Checkout Session for one-time or subscription payments"""
    try:
        if not stripe.api_key:
            raise HTTPException(status_code=500, detail="Stripe not configured")
        
        line_items = []
        
        if data.price_id:
            # Use existing Stripe Price ID
            line_items.append({
                "price": data.price_id,
                "quantity": 1
            })
        elif data.amount:
            # Create price on the fly
            line_items.append({
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": data.product_name,
                    },
                    "unit_amount": data.amount,
                },
                "quantity": 1
            })
        else:
            raise HTTPException(status_code=400, detail="Either price_id or amount is required")
        
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=line_items,
            mode="payment",
            success_url=data.success_url,
            cancel_url=data.cancel_url,
            metadata=data.metadata or {}
        )
        
        return {
            "session_id": session.id,
            "url": session.url
        }
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/create-payment-intent")
async def create_payment_intent(data: CreatePaymentIntent):
    """Create a Payment Intent for custom payment flows"""
    try:
        if not stripe.api_key:
            raise HTTPException(status_code=500, detail="Stripe not configured")
        
        intent = stripe.PaymentIntent.create(
            amount=data.amount,
            currency=data.currency,
            description=data.description,
            metadata=data.metadata or {},
            automatic_payment_methods={"enabled": True}
        )
        
        return {
            "client_secret": intent.client_secret,
            "payment_intent_id": intent.id
        }
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks for payment events"""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    endpoint_secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
    
    try:
        if endpoint_secret:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        else:
            # For testing without webhook signature verification
            import json
            event = json.loads(payload)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Handle specific event types
    event_type = event.get("type", "")
    
    if event_type == "checkout.session.completed":
        session = event["data"]["object"]
        # Handle successful checkout
        print(f"Checkout completed: {session.get('id')}")
        # TODO: Update user subscription status, send confirmation email, etc.
        
    elif event_type == "payment_intent.succeeded":
        payment_intent = event["data"]["object"]
        print(f"Payment succeeded: {payment_intent.get('id')}")
        # TODO: Fulfill order, update database, etc.
        
    elif event_type == "payment_intent.payment_failed":
        payment_intent = event["data"]["object"]
        print(f"Payment failed: {payment_intent.get('id')}")
        # TODO: Notify user of failed payment
    
    return {"status": "success"}

@router.get("/payment-history")
async def get_payment_history(limit: int = 10):
    """Get recent payment history (admin only)"""
    try:
        if not stripe.api_key:
            raise HTTPException(status_code=500, detail="Stripe not configured")
        
        payments = stripe.PaymentIntent.list(limit=limit)
        
        return {
            "payments": [
                {
                    "id": p.id,
                    "amount": p.amount / 100,  # Convert to dollars
                    "currency": p.currency,
                    "status": p.status,
                    "created": datetime.fromtimestamp(p.created, tz=timezone.utc).isoformat(),
                    "description": p.description
                }
                for p in payments.data
            ]
        }
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/balance")
async def get_stripe_balance():
    """Get current Stripe balance (admin only)"""
    try:
        if not stripe.api_key:
            raise HTTPException(status_code=500, detail="Stripe not configured")
        
        balance = stripe.Balance.retrieve()
        
        return {
            "available": [
                {"amount": b.amount / 100, "currency": b.currency}
                for b in balance.available
            ],
            "pending": [
                {"amount": b.amount / 100, "currency": b.currency}
                for b in balance.pending
            ]
        }
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Premium feature pricing (max $24.97 for protocols)
PREMIUM_PRICES = {
    "protocol_basic": {"name": "Basic Protocol", "amount": 299},  # $2.99
    "protocol_standard": {"name": "Standard Protocol", "amount": 799},  # $7.99
    "protocol_pro": {"name": "Pro Protocol", "amount": 1499},  # $14.99
    "protocol_premium": {"name": "Premium Protocol", "amount": 2497},  # $24.97 (max)
}

@router.get("/prices")
async def get_prices():
    """Get available pricing options"""
    return {
        "prices": PREMIUM_PRICES,
        "currency": "usd"
    }
