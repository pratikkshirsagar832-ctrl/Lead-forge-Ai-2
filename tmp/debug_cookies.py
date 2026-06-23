"""Debug cookie loading - why is li_at not persisting?"""
import asyncio, json, sys
sys.path.insert(0, "/root/leadforge/backend")

from linkedin_scraper.core.browser import BrowserManager

SESSION_FILE = "/app/sessions/linkedin_session_8627ce24-6bd5-48b7-9b1f-595d042bfcf6.json"

async def main():
    async with BrowserManager(headless=True, viewport={"width": 1920, "height": 1080}) as browser:
        # Load cookies
        with open(SESSION_FILE) as f:
            data = json.load(f)
        cookies = data.get("cookies", data) if isinstance(data, dict) else data
        if isinstance(cookies, list):
            await browser.context.add_cookies(cookies)
            print(f"Added {len(cookies)} cookies")

        # Check cookies BEFORE navigation
        ctx_cookies = await browser.context.cookies()
        li_at = [c for c in ctx_cookies if c['name'] == 'li_at']
        print(f"\nBefore nav - total: {len(ctx_cookies)}, li_at: {len(li_at)}")
        if li_at:
            print(f"  li_at domain={li_at[0]['domain']}, value={li_at[0]['value'][:20]}...")
        else:
            print("  NO li_at in context!")
            # Print all cookies
            for c in ctx_cookies:
                print(f"  {c['name']:25s} domain={c['domain']:25s}")

        # Navigate to feed
        resp = await browser.page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=30000)
        print(f"\nAfter nav - URL: {browser.page.url} (status: {resp.status if resp else 'N/A'})")

        # Check cookies AFTER navigation
        ctx_cookies2 = await browser.context.cookies()
        li_at2 = [c for c in ctx_cookies2 if c['name'] == 'li_at']
        print(f"\nAfter nav - total: {len(ctx_cookies2)}, li_at: {len(li_at2)}")
        if li_at2:
            print(f"  li_at domain={li_at2[0]['domain']}, value={li_at2[0]['value'][:20]}...")
        else:
            print("  NO li_at after nav!")

        from linkedin_scraper.core.auth import is_logged_in
        print(f"\nLogged in: {await is_logged_in(browser.page)}")

if __name__ == "__main__":
    asyncio.run(main())
