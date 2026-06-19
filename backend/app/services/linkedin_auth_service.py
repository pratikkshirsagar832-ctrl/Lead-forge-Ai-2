import asyncio
import logging
from json import dump, load
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
    def __init__(self, cookie_dir: str = "./sessions"):
        self.cookie_dir = Path(cookie_dir)
        self.cookie_dir.mkdir(parents=True, exist_ok=True)
        self.session_file = self.cookie_dir / "linkedin_session.json"

    def save_cookies(self, cookies: list[dict]) -> None:
        sanitized = self._sanitize_cookies(cookies)
        with open(self.session_file, "w") as f:
            dump({"cookies": sanitized}, f)
        logger.info(f"Saved {len(sanitized)} LinkedIn cookies to {self.session_file}")

    def load_cookies(self) -> list[dict] | None:
        if not self.session_file.exists():
            return None
        try:
            with open(self.session_file) as f:
                data = load(f)
            raw = data.get("cookies", [])
            linkedin = [c for c in raw if "linkedin" in c.get("domain", "").lower()]
            if not linkedin:
                return None
            allowed = {"name", "value", "domain", "path", "expires", "httpOnly", "secure", "sameSite"}
            return self._sanitize_cookies([
                {k: v for k, v in c.items() if k in allowed and v is not None}
                for c in linkedin
            ])
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

    async def login_flow(self, email: str, password: str) -> bool:
        from patchright.sync_api import sync_playwright

        logger.info("Logging into LinkedIn with headless browser...")

        def _login():
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=["--no-sandbox", "--disable-setuid-sandbox"],
                )
                context = browser.new_context(
                    viewport={"width": 1280, "height": 720},
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/125.0.0.0 Safari/537.36"
                    ),
                )
                page = context.new_page()
                page.goto("https://www.linkedin.com/login", timeout=60000)
                page.fill("#username", email)
                page.fill("#password", password)
                page.click("button[type=submit]")

                try:
                    page.wait_for_function(
                        "() => document.cookie.includes('li_at=')",
                        timeout=60000,
                    )
                    cookies = context.cookies()
                    self.save_cookies([
                        {"name": c["name"], "value": c["value"], "domain": c["domain"],
                         "path": c.get("path", "/"), "httpOnly": c.get("httpOnly", False),
                         "secure": c.get("secure", False), "sameSite": c.get("sameSite", "Lax")}
                        for c in cookies
                    ])
                    browser.close()
                    return True
                except Exception as e:
                    cookies = context.cookies()
                    if any(c.get("name") == "li_at" for c in cookies):
                        self.save_cookies([
                            {"name": c["name"], "value": c["value"], "domain": c["domain"],
                             "path": c.get("path", "/"), "httpOnly": c.get("httpOnly", False),
                             "secure": c.get("secure", False), "sameSite": c.get("sameSite", "Lax")}
                            for c in cookies
                        ])
                        browser.close()
                        return True
                    browser.close()
                    return False

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, _login)
        return result

    @staticmethod
    def _sanitize_cookies(cookies: list[dict]) -> list[dict]:
        sanitized = []
        for c in cookies:
            c = dict(c)
            ss = c.get("sameSite", "")
            if ss and ss.lower() in SAMESITE_MAP:
                c["sameSite"] = SAMESITE_MAP[ss.lower()]
            elif not ss or ss.lower() not in ("lax", "strict", "none"):
                c["sameSite"] = "Lax"
            sanitized.append(c)
        return sanitized
