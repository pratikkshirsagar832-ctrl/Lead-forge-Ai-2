"""Check if LinkedIn session cookies actually work via HTTPX."""
import json, asyncio, httpx

SESSION_FILE = "/app/sessions/linkedin_session_8627ce24-6bd5-48b7-9b1f-595d042bfcf6.json"

async def check():
    with open(SESSION_FILE) as f:
        data = json.load(f)
    cookies = data.get("cookies", data) if isinstance(data, dict) else data

    # Build cookie string
    cookie_parts = []
    li_at_val = None
    for c in cookies:
        if c.get("name") and c.get("value"):
            cookie_parts.append(f"{c['name']}={c['value']}")
            if c["name"] == "li_at":
                li_at_val = c["value"]

    cookie_str = "; ".join(cookie_parts)
    print(f"li_at: {li_at_val[:30] if li_at_val else 'N/A'}...")
    print(f"Total cookies in string: {len(cookie_parts)}")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
        "Cookie": cookie_str,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    async with httpx.AsyncClient(timeout=15, follow_redirects=False) as client:
        resp = await client.get("https://www.linkedin.com/feed/", headers=headers)
        print(f"\nFeed status: {resp.status_code}")
        print(f"Location: {resp.headers.get('location', 'N/A')}")
        print(f"Final URL: {resp.url}")

        if resp.status_code in (301, 302, 303, 307):
            loc = resp.headers.get("location", "")
            if "login" in loc.lower():
                print("SESSION INVALID - redirected to login")
            else:
                print(f"Redirected to: {loc}")
        elif resp.status_code < 400:
            print("SESSION VALID - got feed page")
            # Check for nav elements
            if 'class="global-nav' in resp.text or 'class="search-global-typeahead' in resp.text:
                print("Confirmed: nav elements found")
            else:
                print("Warning: no nav elements found but status OK")
        else:
            print(f"Unexpected status: {resp.status_code}")

if __name__ == "__main__":
    asyncio.run(check())
