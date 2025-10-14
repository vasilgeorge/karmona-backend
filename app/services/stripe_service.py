"""
Stripe service for payment processing and subscription management.
"""

import stripe
from typing import Optional

from app.core.config import settings

# Initialize Stripe with secret key
stripe.api_key = settings.stripe_secret_key


class StripeService:
    """Service for Stripe payment and subscription management."""
    
    @staticmethod
    def create_customer(email: str, name: str, user_id: str) -> stripe.Customer:
        """Create a Stripe customer."""
        return stripe.Customer.create(
            email=email,
            name=name,
            metadata={"karmona_user_id": user_id}
        )
    
    @staticmethod
    def create_checkout_session(
        customer_id: str,
        price_id: str,
        success_url: str,
        cancel_url: str,
        user_id: str
    ) -> stripe.checkout.Session:
        """Create a Stripe Checkout Session for subscription."""
        return stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[
                {
                    "price": price_id,
                    "quantity": 1,
                }
            ],
            mode="subscription",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={"karmona_user_id": user_id},
            subscription_data={
                "metadata": {"karmona_user_id": user_id}
            }
        )
    
    @staticmethod
    def create_portal_session(customer_id: str, return_url: str) -> stripe.billing_portal.Session:
        """Create a Stripe Customer Portal session for managing subscription."""
        return stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url,
        )
    
    @staticmethod
    def get_subscription(subscription_id: str) -> Optional[stripe.Subscription]:
        """Get a subscription by ID."""
        try:
            return stripe.Subscription.retrieve(subscription_id)
        except stripe.error.StripeError:
            return None
    
    @staticmethod
    def cancel_subscription(subscription_id: str) -> stripe.Subscription:
        """Cancel a subscription."""
        return stripe.Subscription.modify(
            subscription_id,
            cancel_at_period_end=True
        )
    
    @staticmethod
    def construct_webhook_event(payload: bytes, sig_header: str):
        """Construct and verify webhook event from Stripe."""
        return stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )

