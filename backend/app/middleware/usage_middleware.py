import logging

from fastapi import Depends, HTTPException, status

from app.database import get_supabase_admin
from app.middleware.auth_middleware import get_current_user

logger = logging.getLogger(__name__)


async def check_search_limit(current_user: dict = Depends(get_current_user)) -> dict:
    supabase = get_supabase_admin()
    user_id = current_user["id"]

    try:
        resp = supabase.rpc("get_remaining_searches", {"p_user_id": user_id}).execute()

        remaining = 0
        if resp and resp.data is not None:
            if isinstance(resp.data, list) and len(resp.data) > 0:
                remaining = resp.data[0].get("get_remaining_searches", 0)
            elif isinstance(resp.data, (int, float)):
                remaining = int(resp.data)

        if remaining <= 0:
            sub_resp = supabase.rpc("get_user_subscription", {"p_user_id": user_id}).execute()
            plan_name = "Free"
            if sub_resp and sub_resp.data:
                if isinstance(sub_resp.data, list) and len(sub_resp.data) > 0:
                    plan_name = sub_resp.data[0].get("plan_name", "Free")
                elif isinstance(sub_resp.data, dict):
                    plan_name = sub_resp.data.get("plan_name", "Free")

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
        return current_user


async def increment_search_usage(current_user: dict = Depends(get_current_user), leads_count: int = 0):
    supabase = get_supabase_admin()
    try:
        supabase.rpc("increment_daily_usage", {
            "p_user_id": current_user["id"],
            "p_searches": 1,
            "p_leads": leads_count,
        }).execute()
    except Exception as e:
        logger.error(f"Failed to increment usage: {e}")
