"""
LedgerGuard AI — Commercial Stripe Monetization & Webhook Engine
Enables SaaS subscription checkouts and handles automated entitlement webhooks.
"""

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel
from app.config import settings

router = APIRouter(prefix="/api/billing", tags=["Monetization & Billing"])

class CheckoutRequest(BaseModel):
    tier: str  # "pro" ($29/mo) or "enterprise" ($99/mo)
    success_url: str
    cancel_url: str

@router.post("/create-checkout-session")
async def create_checkout_session(payload: CheckoutRequest):
    """
    Creates a Stripe Checkout Session or returns a simulated test session
    if Stripe credentials are in sandbox/demo mode.
    """
    tier_prices = {
        "pro": {"name": "LedgerGuard Pro (Unlimited Audits & Vault)", "price": 29.00},
        "enterprise": {"name": "LedgerGuard Enterprise (Team Seats & Webhooks)", "price": 99.00}
    }

    tier_info = tier_prices.get(payload.tier.lower(), tier_prices["pro"])

    if settings.STRIPE_SECRET_KEY and not settings.STRIPE_SECRET_KEY.startswith("sk_test_your"):
        try:
            import stripe
            stripe.api_key = settings.STRIPE_SECRET_KEY
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": tier_info["name"],
                            "description": "Automated Accounts Payable Invoice & Wire Fraud Defense Platform"
                        },
                        "unit_amount": int(tier_info["price"] * 100),
                        "recurring": {"interval": "month"}
                    },
                    "quantity": 1,
                }],
                mode="subscription",
                success_url=payload.success_url + "?session_id={CHECKOUT_SESSION_ID}",
                cancel_url=payload.cancel_url,
            )
            return {"checkout_url": session.url, "session_id": session.id, "mode": "live"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Stripe Gateway Error: {str(e)}")

    # Demo/Sandbox Mode (Ready to demo without credit card lockouts)
    return {
        "checkout_url": f"{payload.success_url}?mock_session=active&tier={payload.tier}",
        "session_id": f"mock_sub_session_{payload.tier}",
        "mode": "sandbox",
        "tier": payload.tier,
        "amount_usd": tier_info["price"],
        "message": "Demo mode active. Connect STRIPE_SECRET_KEY in .env for live card transactions."
    }

@router.post("/webhook")
async def stripe_webhook(request: Request):
    """Handles Stripe recurring billing and subscription renewal events."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    # In sandbox/demo mode
    if not settings.STRIPE_WEBHOOK_SECRET or settings.STRIPE_WEBHOOK_SECRET.startswith("whsec_your"):
        return {"status": "success", "mode": "sandbox_acknowledged"}

    try:
        import stripe
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
        return {"status": "success", "event_type": event["type"]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Webhook Signature Verification Failed: {str(e)}")
