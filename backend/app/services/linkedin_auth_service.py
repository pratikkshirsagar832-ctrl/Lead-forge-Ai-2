import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

SAMESITE_MAP = {
    "no_restriction": "None",
    "unspecified": "Lax",
    "none": "None",
    "lax": "Lax",
    "strict": "Strict",
}


class LinkedInSessionManager:
    def __init__(self, cookie_dir: str = "./sessions", user_id: str = ""):
        self.cookie_dir = Path(cookie_dir)
        self.cookie_dir.mkdir(parents=True, exist_ok=True)
        suffix = f"_{user_id}" if user_id else ""
        self.session_file = self.cookie_dir / f"linkedin_session{suffix}.json"

    def save_cookies(self, cookies: list[dict]) -> None:
        normalized = self._normalize_cookies(cookies)
        with open(self.session_file, "w") as f:
            json.dump({"cookies": normalized}, f)
        logger.info(f"Saved {len(normalized)} LinkedIn cookies to {self.session_file}")

    def load_cookies(self) -> list[dict] | None:
        if not self.session_file.exists():
            return None
        try:
            with open(self.session_file) as f:
                data = json.load(f)
            raw = data.get("cookies", [])
            linkedin = [c for c in raw if "linkedin" in c.get("domain", "").lower()]
            if not linkedin:
                return None
            return self._normalize_cookies(linkedin)
        except Exception as e:
            logger.warning(f"Failed to load LinkedIn cookies: {e}")
            return None

    def is_logged_in(self) -> bool:
        if not self.session_file.exists():
            return False
        try:
            cookies = self.load_cookies()
            if not cookies:
                return False
            return any(c.get("name") == "li_at" for c in cookies)
        except Exception:
            return False

    def validate_cookies(self, cookies: list[dict]) -> bool:
        return any(c.get("name") == "li_at" for c in cookies)

    def get_session_age(self) -> int | None:
        if not self.session_file.exists():
            return None
        try:
            mtime = self.session_file.stat().st_mtime
            import time
            return int(time.time() - mtime)
        except Exception:
            return None

    @staticmethod
    def _normalize_cookies(cookies: list[dict]) -> list[dict]:
        normalized = []
        for c in cookies:
            c = dict(c)
            if "expirationDate" in c and "expires" not in c:
                c["expires"] = int(c.pop("expirationDate"))
            if "expires" in c and isinstance(c["expires"], float):
                c["expires"] = int(c["expires"])
            ss = c.get("sameSite", "")
            if ss and ss.lower() in SAMESITE_MAP:
                c["sameSite"] = SAMESITE_MAP[ss.lower()]
            elif not ss or ss.lower() not in ("lax", "strict", "none"):
                c["sameSite"] = "Lax"
            normalized.append(c)
        return normalized
