import json, httpx, asyncio, re

async def main():
    f = open("/app/sessions/linkedin_session_8627ce24-6bd5-48b7-9b1f-595d042bfcf6.json")
    d = json.load(f)
    cookies_list = d.get("cookies", [])

    cj = httpx.Cookies()
    for c in cookies_list:
        name = c.get("name")
        value = c.get("value")
        if name and value:
            cj.set(name, value, domain=".linkedin.com", path="/")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

    async with httpx.AsyncClient(timeout=30, follow_redirects=True, cookies=cj) as client:
        resp = await client.get(
            "https://www.linkedin.com/search/results/content/?keywords=looking+for+web+developer&sortBy=date&datePosted=past-24h",
            headers=headers,
        )
        print(f"Status: {resp.status_code}")
        print(f"Final URL: {resp.url}")
        print(f"History: {len(resp.history)} redirects")
        for h in resp.history:
            print(f"  {h.status_code} -> {h.headers.get('location', 'N/A')}")

        html = resp.text
        print(f"HTML length: {len(html)}")

        if "login" in resp.url.host or "login" in resp.url.path or "uas/login" in str(resp.url):
            print("RESULT: Redirected to LOGIN")
            return

        urns = set(re.findall(r"urn:li:activity:\d+", html))
        print(f"Found {len(urns)} activity URNs")

        text_match = re.findall(r"data-urn=\"(urn:li:activity:\d+)\"", html)
        print(f"Found {len(text_match)} data-urn matches")

        if urns:
            for urn in list(urns)[:3]:
                print(f"  {urn}")

        search_results = re.findall(r'search-results__result-info|search-entity|entity-result|feed-shared-update-v2', html)
        print(f"Search result markers: {len(search_results)}")

asyncio.run(main())
