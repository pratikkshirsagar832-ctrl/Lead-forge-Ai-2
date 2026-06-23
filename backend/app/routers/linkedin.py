import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.middleware.auth_middleware import get_current_user
from app.services.linkedin_auth_service import LinkedInSessionManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/linkedin", tags=["LinkedIn"])

_session_managers: dict[str, LinkedInSessionManager] = {}


def _get_session_manager(user_id: str) -> LinkedInSessionManager:
    if user_id not in _session_managers:
        _session_managers[user_id] = LinkedInSessionManager(user_id=user_id)
    return _session_managers[user_id]


@router.get("/session/status")
async def session_status(current_user: dict = Depends(get_current_user)):
    try:
        mgr = _get_session_manager(current_user["id"])
        return {
            "logged_in": mgr.is_logged_in(),
            "session_file_exists": mgr.session_file.exists(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/info")
async def session_info(current_user: dict = Depends(get_current_user)):
    try:
        mgr = _get_session_manager(current_user["id"])
        logged_in = mgr.is_logged_in()
        age = mgr.get_session_age()
        return {
            "logged_in": logged_in,
            "session_age_seconds": age,
            "session_age_hours": round(age / 3600, 1) if age is not None else None,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class CookieImportRequest(BaseModel):
    cookies: list[dict]


SAMESITE_MAP = {
    "no_restriction": "None",
    "unspecified": "Lax",
    "none": "None",
    "lax": "Lax",
    "strict": "Strict",
}


def _sanitize_cookies(cookies: list[dict]) -> list[dict]:
    sanitized = []
    for c in cookies:
        entry = dict(c)
        if "expirationDate" in entry and "expires" not in entry:
            entry["expires"] = int(entry.pop("expirationDate"))
        if "expires" in entry and isinstance(entry["expires"], float):
            entry["expires"] = int(entry["expires"])
        ss = entry.get("sameSite", "")
        if ss and ss.lower() in SAMESITE_MAP:
            entry["sameSite"] = SAMESITE_MAP[ss.lower()]
        elif not ss or ss.lower() not in ("lax", "strict", "none"):
            entry["sameSite"] = "Lax"
        sanitized.append(entry)
    return sanitized


@router.post("/session/import-cookies")
async def import_cookies(req: CookieImportRequest, current_user: dict = Depends(get_current_user)):
    try:
        sanitized = _sanitize_cookies(req.cookies)
        mgr = _get_session_manager(current_user["id"])
        mgr.save_cookies(sanitized)
        valid = mgr.validate_cookies(sanitized)
        if valid:
            return {"success": True, "message": "LinkedIn session imported successfully."}
        else:
            return {
                "success": False,
                "message": "li_at cookie not found. Please export cookies from a logged-in LinkedIn session.",
            }
    except Exception as e:
        logger.error(f"Cookie import failed for user {current_user['id']}: {e}")
        raise HTTPException(status_code=500, detail="Failed to import cookies")


@router.post("/session/logout")
async def session_logout(current_user: dict = Depends(get_current_user)):
    try:
        mgr = _get_session_manager(current_user["id"])
        if mgr.session_file.exists():
            mgr.session_file.unlink()
        _session_managers.pop(current_user["id"], None)
        return {"success": True, "message": "Logged out of LinkedIn session."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
