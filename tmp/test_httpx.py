import json, httpx, asyncio

async def main():
    f = open("/app/sessions/linkedin_session_8627ce24-6bd5-48b7-9b1f-595d042bfcf6.json")
    d = json.load(f)
    cookies = d.get("cookies", [])

    li_at = [c for c in cookies if c.get("name") == "li_at"]
    print("li_at value:", li_at[0].get("value", "")[:20] if li_at else "MISSING")

    cookie_str = "; ".join(f"{c['name']}={c['value']}" for c in cookies if c.get("name") and c.get("value"))

    async with httpx.AsyncClient(timeout=15, follow_redirects=False) as client:
        resp = await client.get(
            "https://www.linkedin.com/feed/",
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Cookie": cookie_str,
                "Accept": "text/html",
            },
        )
        print(f"Status: {resp.status_code}")
        loc = resp.headers.get("location", "(none)")
        print(f"Location: {loc}")

        if "login" in loc.lower():
            print("RESULT: Redirected to LOGIN")
        elif "/feed/" in loc.lower() or resp.status_code < 400:
            print("RESULT: Valid session (redirect to feed or OK)")
        else:
            print("RESULT: Unknown")

asyncio.run(main())
