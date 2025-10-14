"""
Payments Router

Handles Stripe subscription checkout, webhooks, and subscription management.
"""

from fastapi import APIRouter, HTTPException, Request, Header
from pydantic import BaseModel

from app.core.auth import CurrentUserId
from app.core.config import settings
from app.services import SupabaseService
from app.services.stripe_service import StripeService

router = APIRouter(prefix="/payments", tags=["payments"])


# Request/Response Models
class CheckoutSessionRequest(BaseModel):
    """Request to create checkout session"""
    success_url: str
    cancel_url: str


class CheckoutSessionResponse(BaseModel):
    """Checkout session URL"""
    checkout_url: str


class PortalSessionResponse(BaseModel):
    """Customer portal session URL"""
    portal_url: str


class SubscriptionStatusResponse(BaseModel):
    """User's subscription status"""
    is_premium: bool
    subscription_status: str
    subscription_tier: str
    period_end: str | None


@router.post("/create-checkout-session", response_model=CheckoutSessionResponse)
async def create_checkout_session(
    request: CheckoutSessionRequest,
    user_id: CurrentUserId,
) -> CheckoutSessionResponse:
    """
    Create a Stripe Checkout Session for premium subscription.
    """
    try:
        supabase_service = SupabaseService()
        stripe_service = StripeService()
        
        # Get user
        user = await supabase_service.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if already premium
        if user.subscription_tier == "premium" and user.subscription_status == "active":
            raise HTTPException(status_code=400, detail="Already subscribed to premium")
        
        # Get or create Stripe customer
        stripe_customer_id = user.stripe_customer_id
        
        if not stripe_customer_id:
            # Create new Stripe customer
            customer = stripe_service.create_customer(
                email=user.email,
                name=user.name,
                user_id=str(user_id)
            )
            stripe_customer_id = customer.id
            
            # Update user with Stripe customer ID
            supabase_service.client.table("users").update({
                "stripe_customer_id": stripe_customer_id
            }).eq("id", str(user_id)).execute()
        
        # Create checkout session
        session = stripe_service.create_checkout_session(
            customer_id=stripe_customer_id,
            price_id=settings.stripe_premium_price_id,
            success_url=request.success_url,
            cancel_url=request.cancel_url,
            user_id=str(user_id)
        )
        
        return CheckoutSessionResponse(checkout_url=session.url)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create checkout session: {str(e)}")


@router.post("/create-portal-session", response_model=PortalSessionResponse)
async def create_portal_session(
    user_id: CurrentUserId,
) -> PortalSessionResponse:
    """
    Create a Stripe Customer Portal session for managing subscription.
    """
    try:
        supabase_service = SupabaseService()
        stripe_service = StripeService()
        
        # Get user
        user = await supabase_service.get_user(user_id)
        if not user or not user.stripe_customer_id:
            raise HTTPException(status_code=404, detail="No Stripe customer found")
        
        # Create portal session
        portal_session = stripe_service.create_portal_session(
            customer_id=user.stripe_customer_id,
            return_url=f"{settings.allowed_origins.split(',')[0]}/account"
        )
        
        return PortalSessionResponse(portal_url=portal_session.url)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create portal session: {str(e)}")


@router.get("/subscription-status", response_model=SubscriptionStatusResponse)
async def get_subscription_status(
    user_id: CurrentUserId,
) -> SubscriptionStatusResponse:
    """Get user's current subscription status."""
    try:
        supabase_service = SupabaseService()
        user = await supabase_service.get_user(user_id)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return SubscriptionStatusResponse(
            is_premium=user.subscription_tier == "premium" and user.subscription_status == "active",
            subscription_status=user.subscription_status or "free",
            subscription_tier=user.subscription_tier or "free",
            period_end=user.subscription_period_end.isoformat() if user.subscription_period_end else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get subscription status: {str(e)}")


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="stripe-signature")
):
    """
    Handle Stripe webhook events.
    
    Events we handle:
    - customer.subscription.created
    - customer.subscription.updated
    - customer.subscription.deleted
    - invoice.payment_succeeded
    - invoice.payment_failed
    """
    try:
        if not stripe_signature:
            raise HTTPException(status_code=400, detail="Missing stripe-signature header")
        
        payload = await request.body()
        stripe_service = StripeService()
        supabase_service = SupabaseService()
        
        # Verify webhook signature
        event = stripe_service.construct_webhook_event(payload, stripe_signature)
        
        print(f"📥 Stripe webhook received: {event['type']}")
        
        # Handle different event types
        if event["type"] in [
            "customer.subscription.created",
            "customer.subscription.updated",
            "customer.subscription.deleted"
        ]:
            subscription = event["data"]["object"]
            user_id = subscription["metadata"].get("karmona_user_id")
            
            if not user_id:
                print(f"⚠️ No karmona_user_id in subscription metadata")
                return {"status": "ignored"}
            
            # Update user subscription status
            update_data = {
                "stripe_subscription_id": subscription["id"],
                "subscription_status": subscription["status"],
                "subscription_tier": "premium" if subscription["status"] == "active" else "free",
                "subscription_period_end": subscription["current_period_end"],
            }
            
            supabase_service.client.table("users").update(update_data).eq(
                "id", user_id
            ).execute()
            
            print(f"✅ Updated user {user_id} subscription to {subscription['status']}")
        
        elif event["type"] == "invoice.payment_failed":
            # Handle failed payment
            subscription_id = event["data"]["object"]["subscription"]
            print(f"⚠️ Payment failed for subscription {subscription_id}")
        
        return {"status": "success"}
        
    except Exception as e:
        print(f"❌ Webhook error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Webhook error: {str(e)}")

