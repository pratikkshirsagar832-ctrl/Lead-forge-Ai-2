import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException

from app.middleware.auth_middleware import get_current_user
from app.services.linkedin_auth_service import LinkedInSessionManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/linkedin", tags=["LinkedIn"])

_session_manager = LinkedInSessionManager()
_login_task = None


@router.get("/session/status")
async def session_status(current_user: dict = Depends(get_current_user)):
    try:
        return {
            "logged_in": _session_manager.is_logged_in(),
            "session_file_exists": _session_manager.session_file.exists(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/info")
async def session_info(current_user: dict = Depends(get_current_user)):
    try:
        logged_in = _session_manager.is_logged_in()
        age = _session_manager.get_session_age()
        return {
            "logged_in": logged_in,
            "session_age_seconds": age,
            "session_age_hours": round(age / 3600, 1) if age is not None else None,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


from pydantic import BaseModel


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
        ss = c.get("sameSite", "")
        if ss and ss.lower() in SAMESITE_MAP:
            c["sameSite"] = SAMESITE_MAP[ss.lower()]
        elif not ss or ss.lower() not in ("lax", "strict", "none"):
            c["sameSite"] = "Lax"
        sanitized.append(c)
    return sanitized


@router.post("/session/import-cookies")
async def import_cookies(req: CookieImportRequest, current_user: dict = Depends(get_current_user)):
    try:
        sanitized = _sanitize_cookies(req.cookies)
        _session_manager.save_cookies(sanitized)
        valid = _session_manager.validate_cookies(sanitized)
        if valid:
            return {"success": True, "message": "LinkedIn session imported successfully."}
        else:
            return {
                "success": False,
                "message": "li_at cookie not found. Please export cookies from a logged-in LinkedIn session.",
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/session/logout")
async def session_logout(current_user: dict = Depends(get_current_user)):
    try:
        if _session_manager.session_file.exists():
            _session_manager.session_file.unlink()
        return {"success": True, "message": "Logged out of LinkedIn session."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/session/login")
async def session_login(req: LoginRequest, current_user: dict = Depends(get_current_user)):
    global _login_task

    if _login_task and not _login_task.done():
        return {"success": False, "message": "Login already in progress"}

    async def run_login():
        return await _session_manager.login_flow(req.email, req.password)

    _login_task = asyncio.create_task(run_login())
    return {"success": True, "message": "Login started. Check status at GET /api/linkedin/session/login-status"}


@router.get("/session/login-status")
async def session_login_status(current_user: dict = Depends(get_current_user)):
    global _login_task
    if not _login_task:
        return {"running": False, "done": False, "success": None}
    if _login_task.done():
        try:
            result = _login_task.result()
            return {"running": False, "done": True, "success": result}
        except Exception as e:
            return {"running": False, "done": True, "success": False, "error": str(e)}
    return {"running": True, "done": False, "success": None}
