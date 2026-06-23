"""Minimal test: just li_at cookie with various domain/path settings."""
import asyncio
from playwright.async_api import async_playwright

LI_AT_VALUE = "AQEDAWIhmMsAdDL6AAABnvSroPIAAAfGLgk8lYA0De6dAk11MtSC2D9PlThFs0qfS_ErgHUWdSIv6qX0WUCrfz0v8PgHUR2AVCJX5-ntbrbBjhRd39PqMF8gHB6XjJF9Vioion9MmsF1uzT2cZ5q2PY"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
        )

        # Test 1: domain = .www.linkedin.com (as in file)
        print("=== Test 1: domain=.www.linkedin.com ===")
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=USER_AGENT,
        )
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
        """)

        await context.add_cookies([{
            "name": "li_at",
            "value": LI_AT_VALUE,
            "domain": ".www.linkedin.com",
            "path": "/",
            "secure": True,
            "httpOnly": True,
            "sameSite": "None",
        }])

        page = await context.new_page()
        resp = await page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=30000)
        print(f"  URL: {page.url}")
        print(f"  Title: {await page.title()}")

        ctx_cookies = await context.cookies()
        li_at = [c for c in ctx_cookies if c['name'] == 'li_at']
        print(f"  li_at: {len(li_at)}")
        await context.close()

        # Test 2: same with JSESSIONID
        print("\n=== Test 2: with JSESSIONID ===")
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=USER_AGENT,
        )
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        """)
        await context.add_cookies([{
            "name": "li_at",
            "value": LI_AT_VALUE,
            "domain": ".www.linkedin.com",
            "path": "/",
            "secure": True,
            "httpOnly": True,
            "sameSite": "None",
        }, {
            "name": "JSESSIONID",
            "value": '"ajax:8927065390049574196"',
            "domain": ".www.linkedin.com",
            "path": "/",
            "secure": True,
            "httpOnly": False,
            "sameSite": "None",
        }])
        page = await context.new_page()
        resp = await page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=30000)
        print(f"  URL: {page.url}")
        print(f"  Title: {await page.title()}")
        ctx_cookies = await context.cookies()
        li_at = [c for c in ctx_cookies if c['name'] == 'li_at']
        print(f"  li_at: {len(li_at)}")
        await context.close()

        # Test 3: domain with .linkedin.com (broader)
        print("\n=== Test 3: domain=.linkedin.com ===")
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=USER_AGENT,
        )
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        """)
        await context.add_cookies([{
            "name": "li_at",
            "value": LI_AT_VALUE,
            "domain": ".linkedin.com",
            "path": "/",
            "secure": True,
            "httpOnly": True,
            "sameSite": "None",
        }, {
            "name": "JSESSIONID",
            "value": '"ajax:8927065390049574196"',
            "domain": ".linkedin.com",
            "path": "/",
            "secure": True,
            "httpOnly": False,
            "sameSite": "None",
        }])
        page = await context.new_page()
        resp = await page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=30000)
        print(f"  URL: {page.url}")
        print(f"  Title: {await page.title()}")
        ctx_cookies = await context.cookies()
        li_at = [c for c in ctx_cookies if c['name'] == 'li_at']
        print(f"  li_at: {len(li_at)}")
        await context.close()

        # Test 4: modify cookie storage via CDP
        print("\n=== Test 4: CDP Network.setCookie ===")
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=USER_AGENT,
        )
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        """)
        page = await context.new_page()
        # Must be on the domain first to set cookies via CDP
        resp = await page.goto("https://www.linkedin.com", wait_until="domcontentloaded", timeout=30000)
        cdp = await context.new_cdp_session(page)
        await cdp.send("Network.setCookie", {
            "name": "li_at",
            "value": LI_AT_VALUE,
            "domain": ".www.linkedin.com",
            "path": "/",
            "secure": True,
            "httpOnly": True,
            "sameSite": "None",
        })
        await page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=30000)
        print(f"  URL: {page.url}")
        print(f"  Title: {await page.title()}")
        ctx_cookies = await context.cookies()
        li_at = [c for c in ctx_cookies if c['name'] == 'li_at']
        print(f"  li_at: {len(li_at)}")
        await context.close()

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
