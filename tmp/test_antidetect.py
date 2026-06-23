"""Test LinkedIn with anti-detection measures."""
import asyncio, json, sys
sys.path.insert(0, "/root/leadforge/backend")

from playwright.async_api import async_playwright

SESSION_FILE = "/app/sessions/linkedin_session_8627ce24-6bd5-48b7-9b1f-595d042bfcf6.json"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"

async def main():
    async with async_playwright() as p:
        # Launch with anti-detection args
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-features=IsolateOrigins,site-per-process",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-web-security",
                "--disable-features=BlockInsecurePrivateNetworkRequests",
            ],
        )

        # Create a context with anti-detection
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=USER_AGENT,
            locale="en-US",
            timezone_id="America/New_York",
        )

        # Anti-detection: remove webdriver property
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
            window.chrome = {runtime: {}};
        """)

        # Load cookies
        with open(SESSION_FILE) as f:
            data = json.load(f)
        cookies_arr = data.get("cookies", data) if isinstance(data, dict) else data
        if isinstance(cookies_arr, list):
            await context.add_cookies(cookies_arr)
            print(f"Loaded {len(cookies_arr)} cookies")

        page = await context.new_page()

        # Navigate to feed
        print("\nNavigating to https://www.linkedin.com/feed/ ...")
        resp = await page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=30000)
        print(f"Final URL: {page.url}")
        print(f"Page title: {await page.title()}")

        from linkedin_scraper.core.auth import is_logged_in
        print(f"Logged in: {await is_logged_in(page)}")

        # Check li_at
        ctx_cookies = await context.cookies()
        li_at = [c for c in ctx_cookies if c['name'] == 'li_at']
        print(f"Context cookies: {len(ctx_cookies)}, li_at: {len(li_at)}")

        if await is_logged_in(page):
            # Try search
            keyword = "need website developer"
            search_url = f"https://www.linkedin.com/search/results/content/?keywords={keyword.replace(' ', '%20')}&origin=GLOBAL_SEARCH_HEADER"
            print(f"\nNavigating to search...")
            await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(3)
            print(f"Search URL: {page.url}")

            # Scroll
            for _ in range(3):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(1.5)

            # Extract posts via JS
            posts = await page.evaluate("""() => {
                const posts = [];
                const seen = new Set();
                const html = document.body.innerHTML;
                const urnMatches = html.matchAll(/urn:li:activity:(\\d+)/g);
                for (const match of urnMatches) {
                    const fullUrn = match[0];
                    if (seen.has(fullUrn)) continue;
                    seen.add(fullUrn);
                    const el = document.querySelector(`[data-urn="${fullUrn}"]`);
                    if (!el) continue;
                    let text = '';
                    const textSelectors = ['.update-components-text', '.feed-shared-update-v2__description', '.feed-shared-text', '.break-words'];
                    for (const sel of textSelectors) {
                        const textEl = el.querySelector(sel);
                        if (textEl) {
                            const t = textEl.innerText?.trim() || '';
                            if (t.length > text.length && t.length > 20) text = t;
                        }
                    }
                    if (!text || text.length < 20) continue;
                    const authorEl = el.querySelector('[class*="actor__name"], [class*="update-components-actor__name"]');
                    const author = authorEl ? authorEl.innerText.trim() : '';
                    posts.push({urn: fullUrn, author, text: text.substring(0, 1000)});
                }
                return posts;
            }""")
            print(f"\nExtracted {len(posts)} posts")
            for i, p in enumerate(posts[:3], 1):
                print(f"\n  [{i}] Author: {p['author']}")
                print(f"      Text: {p['text'][:150]}...")
        else:
            print("\nSession not valid. Trying with headful...")

        await context.close()
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
