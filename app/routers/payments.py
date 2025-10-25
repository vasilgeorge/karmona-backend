"""
Payments Router

Handles Stripe subscription checkout, webhooks, and subscription management.
Also handles Apple In-App Purchase verification for iOS subscriptions.
"""

from fastapi import APIRouter, HTTPException, Request, Header
from pydantic import BaseModel
import httpx
from datetime import datetime

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
    cancel_at_period_end: bool


@router.post("/create-checkout-session", response_model=CheckoutSessionResponse)
async def create_checkout_session(
    request: CheckoutSessionRequest,
    user_id: CurrentUserId,
) -> CheckoutSessionResponse:
    """
    Create a Stripe Checkout Session for premium subscription.
    """
    try:
        # Check if Stripe is configured
        if not settings.stripe_secret_key or not settings.stripe_premium_price_id:
            raise HTTPException(
                status_code=503,
                detail="Payment system is being configured. Please check back soon!"
            )
        
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
            
            print(f"📝 Created Stripe customer {stripe_customer_id} for user {user_id}")
            
            # Update user with Stripe customer ID
            result = supabase_service.client.table("users").update({
                "stripe_customer_id": stripe_customer_id
            }).eq("id", str(user_id)).execute()
            
            print(f"💾 Saved customer ID to database: {result.data}")
        
        # Create checkout session
        session = stripe_service.create_checkout_session(
            customer_id=stripe_customer_id,
            price_id=settings.stripe_premium_price_id,
            success_url=request.success_url,
            cancel_url=request.cancel_url,
            user_id=str(user_id)
        )
        
        print(f"✅ Created checkout session for user {user_id}, customer {stripe_customer_id}")
        
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
            period_end=user.subscription_period_end.isoformat() if user.subscription_period_end else None,
            cancel_at_period_end=user.cancel_at_period_end or False
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get subscription status: {str(e)}")


@router.post("/sync-subscription")
async def sync_subscription(user_id: CurrentUserId):
    """
    Manually sync subscription status from Stripe.
    Call this after checkout success to immediately update user status.
    """
    try:
        if not settings.stripe_secret_key:
            raise HTTPException(status_code=503, detail="Stripe not configured")
        
        supabase_service = SupabaseService()
        stripe_service = StripeService()
        
        # Get user
        user = await supabase_service.get_user(user_id)
        if not user or not user.stripe_customer_id:
            raise HTTPException(status_code=404, detail="No Stripe customer found")
        
        # Get customer's subscriptions from Stripe
        import stripe
        subscriptions = stripe.Subscription.list(customer=user.stripe_customer_id, limit=1)
        
        if subscriptions.data:
            subscription = subscriptions.data[0]
            
            # Update user subscription status
            from datetime import datetime
            period_end_timestamp = subscription.current_period_end
            period_end_dt = datetime.fromtimestamp(period_end_timestamp)
            
            update_data = {
                "stripe_subscription_id": subscription.id,
                "subscription_status": subscription.status,
                "subscription_tier": "premium" if subscription.status == "active" else "free",
                "subscription_period_end": period_end_dt.isoformat(),
            }
            
            print(f"💾 Updating user {user_id} with: {update_data}")
            
            result = supabase_service.client.table("users").update(update_data).eq(
                "id", str(user_id)
            ).execute()
            
            print(f"✅ Sync complete. Updated data: {result.data}")
            
            return {"status": "synced", "subscription_status": subscription.status}
        else:
            # No active subscription
            supabase_service.client.table("users").update({
                "subscription_status": "free",
                "subscription_tier": "free",
            }).eq("id", str(user_id)).execute()
            
            return {"status": "synced", "subscription_status": "free"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sync subscription: {str(e)}")


@router.post("/cancel-subscription")
async def cancel_subscription(user_id: CurrentUserId):
    """Cancel user's subscription (at period end)"""
    try:
        if not settings.stripe_secret_key:
            raise HTTPException(status_code=503, detail="Stripe not configured")
        
        supabase_service = SupabaseService()
        stripe_service = StripeService()
        
        # Get user
        user = await supabase_service.get_user(user_id)
        if not user or not user.stripe_subscription_id:
            raise HTTPException(status_code=404, detail="No active subscription found")
        
        # Cancel subscription at period end
        updated_subscription = stripe_service.cancel_subscription(user.stripe_subscription_id)
        
        # Update local database flag
        supabase_service.client.table("users").update({
            "cancel_at_period_end": True
        }).eq("id", str(user_id)).execute()
        
        return {"status": "cancelled", "message": "Subscription will cancel at period end"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel subscription: {str(e)}")


@router.post("/reactivate-subscription")
async def reactivate_subscription(user_id: CurrentUserId):
    """Reactivate a cancelled subscription (undo cancellation)"""
    try:
        if not settings.stripe_secret_key:
            raise HTTPException(status_code=503, detail="Stripe not configured")
        
        supabase_service = SupabaseService()
        stripe_service = StripeService()
        
        # Get user
        user = await supabase_service.get_user(user_id)
        if not user or not user.stripe_subscription_id:
            raise HTTPException(status_code=404, detail="No subscription found")
        
        # Reactivate subscription
        stripe_service.reactivate_subscription(user.stripe_subscription_id)
        
        # Update local database flag
        supabase_service.client.table("users").update({
            "cancel_at_period_end": False
        }).eq("id", str(user_id)).execute()
        
        return {"status": "reactivated", "message": "Subscription reactivated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reactivate subscription: {str(e)}")


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
            from datetime import datetime
            
            # Get period end from subscription items (new API structure)
            period_end_timestamp = None
            if subscription.get("items") and subscription["items"]["data"]:
                period_end_timestamp = subscription["items"]["data"][0].get("current_period_end")
            
            # Fallback to direct field if exists (old API)
            if not period_end_timestamp:
                period_end_timestamp = subscription.get("current_period_end")
            
            update_data = {
                "stripe_subscription_id": subscription["id"],
                "subscription_status": subscription["status"],
                "subscription_tier": "premium" if subscription["status"] == "active" else "free",
                "cancel_at_period_end": subscription.get("cancel_at_period_end", False),
            }
            
            # Add period end if available
            if period_end_timestamp:
                period_end_dt = datetime.fromtimestamp(period_end_timestamp)
                update_data["subscription_period_end"] = period_end_dt.isoformat()
            
            result = supabase_service.client.table("users").update(update_data).eq(
                "id", user_id
            ).execute()
            
            print(f"✅ Updated user {user_id} subscription to {subscription['status']}")
            print(f"   Update result: {result.data}")
        
        elif event["type"] == "invoice.payment_failed":
            # Handle failed payment
            subscription_id = event["data"]["object"]["subscription"]
            print(f"⚠️ Payment failed for subscription {subscription_id}")
        
        return {"status": "success"}
        
    except Exception as e:
        print(f"❌ Webhook error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Webhook error: {str(e)}")


# ============================================================================
# Apple In-App Purchase Endpoints
# ============================================================================

class ApplePurchaseRequest(BaseModel):
    """Request to verify Apple IAP receipt"""
    receipt: str
    productId: str
    transactionId: str


class ApplePurchaseResponse(BaseModel):
    """Apple purchase verification response"""
    verified: bool
    is_premium: bool
    expires_at: str | None


@router.post("/verify-apple-purchase", response_model=ApplePurchaseResponse)
async def verify_apple_purchase(
    request: ApplePurchaseRequest,
    user_id: CurrentUserId,
) -> ApplePurchaseResponse:
    """
    Verify Apple In-App Purchase receipt and activate premium subscription.

    This endpoint:
    1. Verifies the receipt with Apple's servers
    2. Checks if it's a valid subscription
    3. Updates the user's subscription status in the database
    """
    try:
        supabase_service = SupabaseService()

        # Get user
        user = await supabase_service.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Verify receipt with Apple
        verification_result = await verify_apple_receipt(request.receipt)

        if not verification_result["verified"]:
            raise HTTPException(
                status_code=400,
                detail="Receipt verification failed"
            )

        # Extract subscription info from verification result
        latest_receipt_info = verification_result.get("latest_receipt_info")
        if not latest_receipt_info or len(latest_receipt_info) == 0:
            raise HTTPException(
                status_code=400,
                detail="No subscription found in receipt"
            )

        # Get the most recent subscription
        subscription = latest_receipt_info[0]

        # Check if subscription is active
        expires_date_ms = int(subscription.get("expires_date_ms", 0))
        expires_at = datetime.fromtimestamp(expires_date_ms / 1000)
        is_active = expires_at > datetime.now()

        # Update user's subscription in database
        update_data = {
            "subscription_tier": "premium" if is_active else "free",
            "subscription_status": "active" if is_active else "expired",
            "subscription_period_end": expires_at.isoformat(),
            "apple_transaction_id": request.transactionId,
            "apple_product_id": request.productId,
        }

        print(f"💾 Updating user {user_id} with Apple IAP: {update_data}")

        result = supabase_service.client.table("users").update(update_data).eq(
            "id", str(user_id)
        ).execute()

        print(f"✅ Apple IAP verified for user {user_id}")

        return ApplePurchaseResponse(
            verified=True,
            is_premium=is_active,
            expires_at=expires_at.isoformat() if is_active else None
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Apple IAP verification error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to verify Apple purchase: {str(e)}"
        )


@router.post("/restore-purchases")
async def restore_apple_purchases(user_id: CurrentUserId):
    """
    Restore Apple In-App Purchases for a user.

    Note: On iOS, the client should send the latest receipt which contains
    all purchase history. This endpoint will validate and restore active subscriptions.
    """
    try:
        supabase_service = SupabaseService()

        # Get user
        user = await supabase_service.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Check if user has Apple transaction ID (previous purchase)
        if not user.apple_transaction_id:
            return {
                "status": "no_purchases",
                "hasPremium": False,
                "message": "No previous purchases found"
            }

        # For now, just return current subscription status
        # In a full implementation, you'd fetch and verify the latest receipt
        is_premium = (
            user.subscription_tier == "premium" and
            user.subscription_status == "active"
        )

        return {
            "status": "success",
            "hasPremium": is_premium,
            "subscription_status": user.subscription_status,
            "expires_at": user.subscription_period_end.isoformat() if user.subscription_period_end else None
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to restore purchases: {str(e)}"
        )


async def verify_apple_receipt(receipt_data: str) -> dict:
    """
    Verify Apple receipt with Apple's verification servers.

    Uses the production server first, then falls back to sandbox for testing.
    """
    # Apple's verification endpoints
    PRODUCTION_URL = "https://buy.itunes.apple.com/verifyReceipt"
    SANDBOX_URL = "https://sandbox.itunes.apple.com/verifyReceipt"

    request_body = {
        "receipt-data": receipt_data,
        "password": settings.apple_shared_secret if hasattr(settings, 'apple_shared_secret') else "",
        "exclude-old-transactions": True
    }

    async with httpx.AsyncClient() as client:
        # Try production first
        response = await client.post(PRODUCTION_URL, json=request_body, timeout=10.0)
        result = response.json()

        # If status is 21007, receipt is from sandbox - try sandbox endpoint
        if result.get("status") == 21007:
            print("📱 Receipt is from sandbox, trying sandbox endpoint")
            response = await client.post(SANDBOX_URL, json=request_body, timeout=10.0)
            result = response.json()

        # Status 0 means success
        if result.get("status") == 0:
            return {
                "verified": True,
                "latest_receipt_info": result.get("latest_receipt_info", []),
                "pending_renewal_info": result.get("pending_renewal_info", [])
            }
        else:
            print(f"❌ Apple receipt verification failed with status {result.get('status')}")
            return {
                "verified": False,
                "error": f"Verification failed with status {result.get('status')}"
            }
