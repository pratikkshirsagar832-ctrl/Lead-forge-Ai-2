"""Check cookie timestamps and HTTPX with follow_redirects=True."""
import json, asyncio, httpx
from datetime import datetime

SESSION_FILE = "/app/sessions/linkedin_session_8627ce24-6bd5-48b7-9b1f-595d042bfcf6.json"

async def main():
    with open(SESSION_FILE) as f:
        data = json.load(f)
    cookies = data.get("cookies", data) if isinstance(data, dict) else data

    print("=== Cookie Expiry Check ===")
    now = datetime.now()
    print(f"Current time: {now}")

    for c in cookies:
        if c.get("expires"):
            dt = datetime.fromtimestamp(c["expires"])
            remaining = dt - now
            if c["name"] in ("li_at", "JSESSIONID", "li_sugr", "bcookie"):
                print(f"{c['name']:20s} expires={dt} remaining={remaining}")

    # HTTPX with follow_redirects=True to see final page
    print("\n=== HTTPX with follow_redirects=True ===")
    cookie_parts = []
    for c in cookies:
        if c.get("name") and c.get("value") and c.get("name") != "__cf_bm":
            cookie_parts.append(f"{c['name']}={c['value']}")
    cookie_str = "; ".join(cookie_parts)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
        "Cookie": cookie_str,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        resp = await client.get("https://www.linkedin.com/feed/", headers=headers)
        print(f"Final status: {resp.status_code}")
        print(f"Final URL: {resp.url}")

        if resp.status_code < 400:
            if 'class="global-nav' in resp.text or 'class="search-global-typeahead' in resp.text:
                print("NAV ELEMENTS FOUND - session is VALID")
            else:
                print("Status OK but no nav elements - check manually")
                # print first 200 chars of body
                print(f"Body: {resp.text[:200]}")
        else:
            print(f"Error response: {resp.text[:200]}")

    # Also try the old test that 'worked' before - simple page.goto with different timing
    print("\n=== Try with different wait_until ===")
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
        )
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
        )
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        """)

        # Filter the cookies to remove the problematic storeId and session fields
        clean_cookies = []
        for c in cookies:
            if c.get("name") in ("li_at", "JSESSIONID", "bcookie", "lidc", "li_sugr", "lang", "liap", "bscookie"):
                clean_cookies.append({
                    "name": c["name"],
                    "value": c["value"],
                    "domain": c.get("domain", ".linkedin.com"),
                    "path": c.get("path", "/"),
                    "secure": c.get("secure", True),
                    "httpOnly": c.get("httpOnly", False),
                    "sameSite": c.get("sameSite", "None"),
                })

        await context.add_cookies(clean_cookies)
        print(f"Added {len(clean_cookies)} clean cookies")

        page = await context.new_page()

        # Try with networkidle instead of domcontentloaded
        resp = await page.goto("https://www.linkedin.com/feed/", wait_until="networkidle", timeout=60000)
        print(f"Final URL: {page.url}")
        print(f"Title: {await page.title()}")

        ctx_cookies = await context.cookies()
        li_at = [c for c in ctx_cookies if c['name'] == 'li_at']
        print(f"li_at after: {len(li_at)}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
