import logging

from fastapi import Depends, HTTPException, status

from app.database import get_supabase_admin
from app.middleware.auth_middleware import get_current_user

logger = logging.getLogger(__name__)


async def check_search_limit(current_user: dict = Depends(get_current_user)) -> dict:
    supabase = get_supabase_admin()
    user_id = current_user["id"]

    try:
        plan_max = 0
        plan_name = "Free"

        sub_resp = supabase.table("user_subscriptions").select("plan_id, status").eq("user_id", user_id).order("created_at", desc=True).limit(1).execute()
        if sub_resp.data and len(sub_resp.data) > 0:
            sub = sub_resp.data[0]
            plan_id = sub.get("plan_id", "free")
            plan_resp = supabase.table("plans").select("searches_per_day, name").eq("id", plan_id).execute()
            if plan_resp.data and len(plan_resp.data) > 0:
                plan_max = plan_resp.data[0].get("searches_per_day", 1)
                plan_name = plan_resp.data[0].get("name", "Free")

        if plan_max <= 0:
            plan_max = 1

        from datetime import date
        today = date.today().isoformat()
        usage_resp = supabase.table("daily_usage").select("searches_run").eq("user_id", user_id).eq("date", today).execute()
        used_today = 0
        if usage_resp.data and len(usage_resp.data) > 0:
            used_today = usage_resp.data[0].get("searches_run", 0) or 0

        remaining = max(0, plan_max - used_today)

        if remaining <= 0:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "message": "Daily search limit reached",
                    "remaining_searches": 0,
                    "plan": plan_name,
                    "upgrade_url": "/pricing",
                },
            )

        return current_user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Usage check error for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify usage limits",
        )


async def increment_search_usage(user_id: str, leads_count: int = 0):
    supabase = get_supabase_admin()
    try:
        supabase.rpc("increment_daily_usage", {
            "p_user_id": user_id,
            "p_searches": 1,
            "p_leads": leads_count,
        }).execute()
    except Exception as e:
        logger.error(f"Failed to increment usage for user {user_id}: {e}")
