"""
InvoiceSnap — Stripe pricing integration.

Pro Plan: $9/month, unlimited invoice extractions.
Free Plan: 3 extractions total (session-based).
"""

import os
import stripe

STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_PRICE_ID = os.environ.get("STRIPE_PRICE_ID", "")  # $9/mo price ID
SITE_URL = os.environ.get("SITE_URL", "http://localhost:8000")

FREE_LIMIT = 3

stripe.api_key = STRIPE_SECRET_KEY


def create_checkout_session() -> str:
    """Create a Stripe Checkout session and return the URL."""
    if not STRIPE_SECRET_KEY or not STRIPE_PRICE_ID:
        raise RuntimeError(
            "Stripe is not configured. Set STRIPE_SECRET_KEY and STRIPE_PRICE_ID env vars."
        )

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[
            {
                "price": STRIPE_PRICE_ID,
                "quantity": 1,
            }
        ],
        mode="subscription",
        success_url=f"{SITE_URL}?checkout=success",
        cancel_url=f"{SITE_URL}?checkout=cancelled",
        metadata={"product": "invoicesnap_pro"},
    )
    return session.url


def verify_usage(session_id: str, used: int) -> bool:
    """Check if user is within their free limit."""
    return used < FREE_LIMIT


def increment_usage(store: dict, session_id: str):
    """Increment usage counter for a session."""
    store[session_id] = store.get(session_id, 0) + 1
