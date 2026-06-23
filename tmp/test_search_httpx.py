import json, httpx, asyncio, re

async def main():
    f = open("/app/sessions/linkedin_session_8627ce24-6bd5-48b7-9b1f-595d042bfcf6.json")
    d = json.load(f)
    cookies_list = d.get("cookies", [])

    cookie_str = "; ".join(f"{c['name']}={c['value']}" for c in cookies_list if c.get("name") and c.get("value"))

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
        "Cookie": cookie_str,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
    }

    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        resp = await client.get(
            "https://www.linkedin.com/search/results/content/?keywords=looking+for+web+developer&sortBy=date&datePosted=past-24h",
            headers=headers,
        )
        print(f"Status: {resp.status_code}")
        print(f"Final URL: {resp.url}")

        html = resp.text
        print(f"HTML length: {len(html)}")

        if "login" in resp.url.host or "login" in resp.url.path:
            print("RESULT: Redirected to LOGIN page")
        else:
            urns = set(re.findall(r"urn:li:activity:\d+", html))
            print(f"Found {len(urns)} activity URNs")

            text_matches = re.findall(r'class="[^"]*update-components-text[^"]*"[^>]*>([^<]+)', html)
            print(f"Found {len(text_matches)} text content matches")

            if urns:
                for urn in list(urns)[:3]:
                    print(f"  Sample: {urn}")
            else:
                content = re.sub(r"<[^>]+>", " ", html)
                content = re.sub(r"\s+", " ", content)
                print(f"Text preview: {content[500:1000]}")

asyncio.run(main())
