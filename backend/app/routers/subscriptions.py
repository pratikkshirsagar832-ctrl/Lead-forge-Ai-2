import hashlib
import hmac
import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.config import get_settings
from app.database import get_supabase_admin
from app.middleware.auth_middleware import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/subscriptions", tags=["Subscriptions"])


@router.get("/plans")
async def list_plans():
    supabase = get_supabase_admin()
    resp = supabase.table("plans").select("*").eq("is_active", True).order("sort_order").execute()
    return {"plans": resp.data or []}


@router.get("/current")
async def get_current_subscription(current_user: dict = Depends(get_current_user)):
    supabase = get_supabase_admin()

    try:
        resp = supabase.rpc(
            "get_user_subscription",
            {"p_user_id": current_user["id"]},
        ).execute()

        if resp and resp.data:
            return resp.data

        return {
            "plan_id": "free",
            "plan_name": "Free",
            "leads_per_day": 10,
            "searches_per_day": 1,
            "status": "trial",
            "remaining_searches": 1,
            "is_trial_expired": False,
        }
    except Exception as e:
        logger.error(f"Failed to get subscription: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch subscription")


@router.post("/create-order")
async def create_order(
    plan_id: str,
    current_user: dict = Depends(get_current_user),
):
    settings = get_settings()

    if not settings.razorpay_key_id or not settings.razorpay_key_secret:
        raise HTTPException(status_code=500, detail="Payments not configured")

    try:
        import razorpay

        client = razorpay.Client(auth=(settings.razorpay_key_id, settings.razorpay_key_secret))

        supabase = get_supabase_admin()
        plan_resp = supabase.table("plans").select("*").eq("id", plan_id).single().execute()
        if not plan_resp.data:
            raise HTTPException(status_code=404, detail="Plan not found")

        plan = plan_resp.data
        amount = plan["price_monthly"]

        if amount <= 0:
            raise HTTPException(status_code=400, detail="Cannot create order for free plan")

        order = client.order.create({
            "amount": amount,
            "currency": "INR",
            "receipt": f"sub_{current_user['id']}_{plan_id}",
            "notes": {
                "user_id": current_user["id"],
                "plan_id": plan_id,
                "plan_name": plan["name"],
            },
        })

        supabase.table("user_subscriptions").update({
            "razorpay_order_id": order["id"],
        }).eq("user_id", current_user["id"]).execute()

        return {
            "order_id": order["id"],
            "amount": amount,
            "currency": "INR",
            "key_id": settings.razorpay_key_id,
            "plan_name": plan["name"],
            "plan_id": plan_id,
        }

    except HTTPException:
        raise
    except ImportError:
        raise HTTPException(status_code=500, detail="Razorpay SDK not installed")
    except Exception as e:
        logger.error(f"Failed to create order: {e}")
        raise HTTPException(status_code=500, detail="Failed to create payment order")


@router.post("/verify")
async def verify_payment(
    data: dict,
    current_user: dict = Depends(get_current_user),
):
    settings = get_settings()

    razorpay_order_id = data.get("razorpay_order_id")
    razorpay_payment_id = data.get("razorpay_payment_id")
    razorpay_signature = data.get("razorpay_signature")
    plan_id = data.get("plan_id")

    if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature, plan_id]):
        raise HTTPException(status_code=400, detail="Missing payment verification fields")

    expected_signature = hmac.new(
        settings.razorpay_key_secret.encode(),
        f"{razorpay_order_id}|{razorpay_payment_id}".encode(),
        hashlib.sha256,
    ).hexdigest()

    if expected_signature != razorpay_signature:
        raise HTTPException(status_code=400, detail="Invalid payment signature")

    supabase = get_supabase_admin()

    plan_resp = supabase.table("plans").select("*").eq("id", plan_id).single().execute()
    if not plan_resp.data:
        raise HTTPException(status_code=404, detail="Plan not found")

    plan = plan_resp.data

    supabase.table("user_subscriptions").update({
        "plan_id": plan_id,
        "status": "active",
        "razorpay_order_id": razorpay_order_id,
        "current_period_start": "now()",
        "current_period_end": f"now() + interval '30 days'",
    }).eq("user_id", current_user["id"]).execute()

    return {
        "status": "success",
        "plan_id": plan_id,
        "plan_name": plan["name"],
        "message": f"Upgraded to {plan['name']} plan",
    }


@router.post("/webhook")
async def razorpay_webhook(request: Request):
    settings = get_settings()

    body = await request.body()
    received_signature = request.headers.get("X-Razorpay-Signature", "")

    if not received_signature:
        raise HTTPException(status_code=400, detail="Missing signature")

    expected_signature = hmac.new(
        settings.razorpay_key_secret.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()

    if received_signature != expected_signature:
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    try:
        event = json.loads(body)
        event_type = event.get("event", "")
        payload = event.get("payload", {})

        logger.info(f"Razorpay webhook: {event_type}")

        if event_type == "payment.captured":
            order_id = payload.get("payment", {}).get("entity", {}).get("order_id", "")
            if order_id:
                supabase = get_supabase_admin()
                supabase.table("user_subscriptions").update({
                    "status": "active",
                }).eq("razorpay_order_id", order_id).execute()

        elif event_type == "subscription.charged":
            sub_id = payload.get("subscription", {}).get("entity", {}).get("id", "")
            if sub_id:
                supabase = get_supabase_admin()
                supabase.table("user_subscriptions").update({
                    "status": "active",
                }).eq("razorpay_subscription_id", sub_id).execute()

        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/cancel")
async def cancel_subscription(current_user: dict = Depends(get_current_user)):
    supabase = get_supabase_admin()

    supabase.table("user_subscriptions").update({
        "status": "cancelled",
        "cancelled_at": "now()",
    }).eq("user_id", current_user["id"]).execute()

    return {"status": "cancelled", "message": "Subscription cancelled"}
