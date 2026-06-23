import json, httpx, asyncio

async def main():
    f = open("/app/sessions/linkedin_session_8627ce24-6bd5-48b7-9b1f-595d042bfcf6.json")
    d = json.load(f)
    cookies_list = d.get("cookies", [])
    cookie_str = "; ".join(f"{c['name']}={c['value']}" for c in cookies_list if c.get("name") and c.get("value"))

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Cookie": cookie_str,
        "Accept": "text/html,application/xhtml+xml",
    }

    async with httpx.AsyncClient(timeout=15, follow_redirects=True, max_redirects=30) as client:
        resp = await client.get(
            "https://www.linkedin.com/feed/",
            headers=headers,
        )
        print(f"Final URL: {resp.url}")
        print(f"Final status: {resp.status_code}")
        print(f"History ({len(resp.history)} redirects):")
        for i, h in enumerate(resp.history):
            print(f"  {i}: {h.status_code} -> {h.headers.get('location', 'N/A')}")

asyncio.run(main())
