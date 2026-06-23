import json, httpx, asyncio, re

async def main():
    f = open("/app/sessions/linkedin_session_8627ce24-6bd5-48b7-9b1f-595d042bfcf6.json")
    d = json.load(f)
    cookies_list = d.get("cookies", [])

    cookie_str = "; ".join(f"{c['name']}={c['value']}" for c in cookies_list if c.get("name") and c.get("value"))

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Cookie": cookie_str,
    }

    async with httpx.AsyncClient(timeout=30, max_redirects=10) as client:
        resp = await client.get(
            "https://www.linkedin.com/search/results/content/?keywords=looking+for+web+developer&sortBy=date&datePosted=past-24h",
            headers=headers,
        )
        print(f"Status: {resp.status_code}")
        print(f"Final URL: {resp.url}")

        html = resp.text
        print(f"HTML length: {len(html)}")

        url_str = str(resp.url)
        if "login" in url_str:
            print("RESULT: Login page")
            return

        urns = set(re.findall(r"urn:li:activity:\d+", html))
        print(f"Found {len(urns)} activity URNs")

        data_urns = re.findall(r'data-urn="(urn:li:activity:\d+)"', html)
        print(f"Found {len(data_urns)} data-urn matches")

        search_results = re.findall(r'search-results__result-info|search-entity|entity-result|feed-shared-update-v2', html)
        print(f"Search result markers: {len(search_results)}")

        if urns:
            for urn in list(urns)[:3]:
                print(f"  {urn}")

asyncio.run(main())
