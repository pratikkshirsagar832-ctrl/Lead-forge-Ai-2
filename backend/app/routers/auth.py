import logging

from fastapi import APIRouter, Depends, HTTPException

from app.database import get_supabase_admin
from app.middleware.auth_middleware import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    supabase = get_supabase_admin()

    try:
        sub_resp = supabase.rpc(
            "get_user_subscription",
            {"p_user_id": current_user["id"]},
        ).execute()

        subscription = sub_resp.data if sub_resp and sub_resp.data else None
    except Exception as e:
        logger.warning(f"Failed to fetch subscription for user {current_user['id']}: {e}")
        subscription = None

    return {
        "id": current_user["id"],
        "email": current_user["email"],
        "name": current_user["name"],
        "subscription": subscription,
    }
