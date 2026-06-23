"""Trace LinkedIn redirect chain to understand why session is rejected."""
import asyncio, json, sys
sys.path.insert(0, "/root/leadforge/backend")

from linkedin_scraper.core.browser import BrowserManager

SESSION_FILE = "/app/sessions/linkedin_session_8627ce24-6bd5-48b7-9b1f-595d042bfcf6.json"

async def main():
    async with BrowserManager(headless=True, viewport={"width": 1920, "height": 1080}) as browser:
        # Load cookies
        with open(SESSION_FILE) as f:
            data = json.load(f)
        cookies_arr = data.get("cookies", data) if isinstance(data, dict) else data
        if isinstance(cookies_arr, list):
            await browser.context.add_cookies(cookies_arr)
            print(f"Loaded {len(cookies_arr)} cookies")

        # Track ALL network responses
        redirect_chain = []
        set_cookie_headers = []

        async def on_response(response):
            req = response.request
            redirect_chain.append({
                "url": response.url,
                "status": response.status,
                "req_url": req.url,
                "req_method": req.method,
            })
            if response.status in (301, 302, 303, 307, 308):
                loc = response.headers.get("location", "")
                redirect_chain[-1]["location"] = loc
            # Check for Set-Cookie
            if "set-cookie" in response.headers:
                cookie_vals = response.headers.get_list("set-cookie")
                for cv in cookie_vals:
                    set_cookie_headers.append({"url": response.url, "cookie": cv})

        browser.page.on("response", on_response)

        # Navigate to feed
        print("\nNavigating to https://www.linkedin.com/feed/ ...")
        resp = await browser.page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=30000)
        print(f"Final URL: {browser.page.url}")
        print(f"Page title: {await browser.page.title()}")

        # Print redirect chain
        print("\n=== Redirect Chain ===")
        for i, r in enumerate(redirect_chain):
            print(f"  [{i}] {r['status']} {r['url'][:80]}")
            if 'location' in r:
                print(f"       -> Location: {r['location'][:80]}")

        # Print Set-Cookie headers
        print("\n=== Set-Cookie Headers ===")
        for sc in set_cookie_headers:
            cookie_name = sc['cookie'].split('=')[0]
            cookie_val = sc['cookie'][:100]
            if 'li_at' in sc['cookie'] or 'li_at' in cookie_name:
                print(f"  ** LI_AT: {cookie_val}")
            elif cookie_name in ('JSESSIONID', 'bcookie', 'lidc'):
                print(f"  {cookie_val}")

        # Check final context cookies
        ctx_cookies = await browser.context.cookies()
        li_at = [c for c in ctx_cookies if c['name'] == 'li_at']
        print(f"\nContext cookies count: {len(ctx_cookies)}, li_at: {len(li_at)}")

if __name__ == "__main__":
    asyncio.run(main())
