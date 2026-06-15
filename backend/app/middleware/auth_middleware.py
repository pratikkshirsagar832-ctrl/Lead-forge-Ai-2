import time
import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.database import get_supabase_admin

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)

_token_cache: dict[str, dict] = {}
CACHE_TTL = 60


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Please log in.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    cached = _token_cache.get(token)
    if cached and cached["expires_at"] > time.time():
        return cached["user"]

    try:
        supabase = get_supabase_admin()
        user_resp = supabase.auth.get_user(token)

        if not user_resp or not user_resp.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token.",
            )

        user = user_resp.user
        result = {
            "id": user.id,
            "email": user.email or "",
            "name": user.user_metadata.get("full_name", user.user_metadata.get("name", user.email or "")),
        }

        try:
            existing = supabase.table("users").select("id").eq("id", user.id).limit(1).execute()
            if not existing.data:
                supabase.table("users").insert({
                    "id": user.id,
                    "email": user.email or "",
                }).execute()
        except Exception as sync_err:
            logger.warning(f"User sync failed (non-critical): {sync_err}")

        try:
            sub_exists = supabase.table("user_subscriptions").select("id").eq("user_id", user.id).limit(1).execute()
            if not sub_exists.data or len(sub_exists.data) == 0:
                from datetime import datetime, timedelta, timezone
                now = datetime.now(timezone.utc)
                supabase.table("user_subscriptions").insert({
                    "user_id": user.id,
                    "plan_id": "free",
                    "status": "trial",
                    "trial_end": (now + timedelta(days=3)).isoformat(),
                    "current_period_end": (now + timedelta(days=3)).isoformat(),
                }).execute()
                logger.info(f"Created free trial subscription for user {user.id}")
        except Exception as sub_err:
            logger.warning(f"Subscription auto-creation failed (non-critical): {sub_err}")

        _token_cache[token] = {"user": result, "expires_at": time.time() + CACHE_TTL}
        return result

    except HTTPException:
        _token_cache.pop(token, None)
        raise
    except Exception as e:
        logger.error(f"Auth error: {e}")
        _token_cache.pop(token, None)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed. Please log in again.",
        )


async def get_current_user_id(current_user: dict = Depends(get_current_user)) -> str:
    return current_user["id"]
