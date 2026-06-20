import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

from app.config import get_settings
from app.database import get_supabase_admin

logger = logging.getLogger(__name__)

TIME_FILTER_MAP = {
    "latest": "%22past-24h%22",
    "7_days": "%22past-week%22",
    "14_days": "%22past-two-weeks%22",
    "27_days": "%22r2592000%22",
    "2_months": "%22r4838400%22",
}

LINKEDIN_SEARCH_URL = (
    "https://www.linkedin.com/search/results/content/"
    "?keywords={keyword}&sortBy=%22date%22&datePosted={time_filter}"
)

def _session_path(user_id: str = "") -> Path:
    suffix = f"_{user_id}" if user_id else ""
    return Path(f"./sessions/linkedin_session{suffix}.json")

PROVIDER_PATTERNS = [
    "i built", "i developed", "i created", "i made", "i launched",
    "i offer", "i provide", "i specialize", "i help",
    "building something similar", "let's talk", "dm me",
    "we built", "we developed", "we create", "we offer", "we provide",
    "looking for clients", "open for work", "available for hire",
    "hire me", "my services", "our services",
    "portfolio", "showcasing", "check my work",
]

LEAD_TYPE_PROMPTS = {
    "all": {
        "query": """You are a LinkedIn search query expert. Return a JSON object with key "queries" containing exactly 10 SHORT search queries (2-5 words each) that find people expressing buying intent.

CRITICAL: Queries must be SHORT (under 40 chars).

Focus on intent signals mixed with job titles:
- "looking for X"
- "need X"
- "hiring X"
- "help X"

Example for "web development":
{"queries": ["looking for web developer", "need react developer", "hiring full stack dev", "help with website", "recommendation web developer", "need ecommerce site", "looking for frontend dev", "hiring software developer", "help with web app", "recommendation for developer"]}

Generate 10 SHORT queries for the topic the user provides.""",
        "extract": """You are analyzing LinkedIn posts for lead generation. Find posts from people who NEED a service or HAVE A PROBLEM — NOT people offering services.

Return JSON with key "leads" containing an array. For each lead:
- "author_name": person's name
- "post_text": main content
- "qualified": true/false
- "confidence": 0.0 to 1.0
- "reason": short explanation

LEAD = looking to hire someone, needs help with a project, has a business problem, asking for recommendations, looking for a freelancer/agency/consultant

NOT LEAD (REJECT THESE):
- "I built X" / "I developed X" / "I created X" — showing off their own work
- "Let's talk" / "DM me" — offering services
- Sharing portfolio or case study of their own work
- Announcing availability for freelance/contract work
- Promoting their agency or services
- Recruiting for their own company (they are the provider of the job)

CRITICAL RULE: If the person is offering a service, selling something, or showing their own work → NOT A LEAD. Only people who need to BUY a service are leads.

Posts:""",
    },
    "intern": {
        "query": """You are a LinkedIn search query expert. Return a JSON object with key "queries" containing exactly 10 SHORT search queries (2-5 words each) that find people offering internships or looking for interns/entry-level talent.

CRITICAL: Queries must be SHORT (under 40 chars).

Focus on:
- "hiring intern"
- "looking for intern"
- "internship opportunity"
- "hiring fresher"
- "looking for trainee"
- "entry level position"
- "graduate intern"
- "internship program"
- "hiring apprentice"
- "need intern"

Example for "web development":
{"queries": ["hiring web dev intern", "looking for frontend intern", "internship web developer", "hiring fresher react", "entry level web dev", "looking for ui ux intern", "internship full stack", "hiring graduate intern", "web development trainee", "need intern developer"]}

Generate 10 SHORT queries for the topic the user provides.""",
        "extract": """You are analyzing LinkedIn posts for lead generation. Find posts where companies are looking to HIRE interns or entry-level talent — NOT posts from individuals offering their services.

Return JSON with key "leads" containing an array. For each lead:
- "author_name": person's name
- "post_text": main content
- "qualified": true/false
- "confidence": 0.0 to 1.0
- "reason": short explanation

LEAD = offering internship position, hiring entry-level, looking for fresher, internship program
NOT LEAD = person looking for internship themselves, showcasing projects, offering services, "DM me"

Posts:""",
    },
    "agency": {
        "query": """You are a LinkedIn search query expert. Return a JSON object with key "queries" containing exactly 10 SHORT search queries (2-5 words each) that find people or businesses looking to hire an agency or external service provider.

CRITICAL: Queries must be SHORT (under 40 chars).

Focus on:
- "looking for agency"
- "need marketing agency"
- "hire design agency"
- "looking for SEO agency"
- "need development agency"
- "hire digital agency"
- "looking for consultancy"
- "need PR agency"
- "hire creative agency"
- "looking for media agency"

Example for "web development":
{"queries": ["looking for web agency", "need web design agency", "hire development agency", "looking for SEO agency", "need digital agency", "hire ui ux agency", "looking for branding agency", "need ecommerce agency", "hire creative agency", "looking for marketing agency"]}

Generate 10 SHORT queries for the topic the user provides.""",
        "extract": """You are analyzing LinkedIn posts for lead generation. Find posts from businesses who NEED to hire an agency — NOT posts from agencies offering services.

Return JSON with key "leads" containing an array. For each lead:
- "author_name": person's name
- "post_text": main content
- "qualified": true/false
- "confidence": 0.0 to 1.0
- "reason": short explanation

LEAD = looking for agency partners, need external help, seeking service provider, want to outsource, need a marketing/design/dev agency

NOT LEAD (REJECT):
- "We are a [type] agency" / "our agency offers" — promoting their own agency
- "I built X for clients" — showing off client work
- "Let's talk if you need X" — offering services
- Case studies or portfolio of agency work

Posts:""",
    },
    "company": {
        "query": """You are a LinkedIn search query expert. Return a JSON object with key "queries" containing exactly 10 SHORT search queries (2-5 words each) that find companies hiring employees or filling full-time positions.

CRITICAL: Queries must be SHORT (under 40 chars).

Focus on:
- "hiring X"
- "looking for X developer"
- "job opening X"
- "we are hiring"
- "full time position"
- "senior X role"
- "join our team"
- "career opportunity"
- "open position"
- "recruiting X"

Example for "web development":
{"queries": ["hiring react developer", "looking for full stack dev", "job opening frontend", "we are hiring web dev", "senior react role", "join our team developer", "full stack position", "career opportunity developer", "open position web", "recruiting software engineer"]}

Generate 10 SHORT queries for the topic the user provides.""",
        "extract": """You are analyzing LinkedIn posts for lead generation. Find posts where companies are hiring full-time employees for their own team.

Return JSON with key "leads" containing an array. For each lead:
- "author_name": person's name
- "post_text": main content
- "qualified": true/false
- "confidence": 0.0 to 1.0
- "reason": short explanation

LEAD = hiring employees for their own company, full-time position, job opening at their firm
NOT = internship, freelance project, agency offering services, recruitment agency posting on behalf of others

Posts:""",
    },
    "one_client": {
        "query": """You are a LinkedIn search query expert. Return a JSON object with key "queries" containing exactly 10 SHORT search queries (2-5 words each) that find individuals or small businesses needing a one-time service or project help.

CRITICAL: Queries must be SHORT (under 40 chars).

Focus on:
- "need website"
- "help with app"
- "looking for freelancer"
- "need graphic designer"
- "help with logo"
- "need developer"
- "looking for consultant"
- "help with automation"
- "need virtual assistant"
- "hire freelancer"

Example for "web development":
{"queries": ["need website built", "help with web app", "looking for freelance dev", "need ecommerce site", "help with landing page", "need react developer", "looking for web consultant", "help redesign website", "need portfolio site", "looking for wordpress help"]}

Generate 10 SHORT queries for the topic the user provides.""",
        "extract": """You are analyzing LinkedIn posts for lead generation. Find posts from individuals or businesses who NEED a freelancer or one-time project help — NOT freelancers offering their services.

Return JSON with key "leads" containing an array. For each lead:
- "author_name": person's name
- "post_text": main content
- "qualified": true/false
- "confidence": 0.0 to 1.0
- "reason": short explanation

LEAD = needs someone to build/design/fix something, looking for a freelancer, has a project they need help with, small business owner needing technical help

NOT LEAD (REJECT):
- "I built X" / "I developed Y" — showing off their own work
- "Available for freelance" — looking for work
- "Let's build something together" — offering services
- Sharing their portfolio or project showcase
- "DM me if you need" — selling services
- "Open for opportunities" — job seeking

CRITICAL: If they are offering to build or have built something for others → NOT a lead. Only people LOOKING to hire someone are leads.

Posts:""",
    },
}


def _is_provider(text: str) -> bool:
    t = text.lower()
    return any(p in t for p in PROVIDER_PATTERNS)


def _load_session_cookies(user_id: str = "") -> list[dict] | None:
    session_file = _session_path(user_id)
    if not session_file.exists():
        return None
    try:
        with open(session_file) as f:
            data = json.load(f)
        raw = data.get("cookies", [])
        linkedin = [c for c in raw if "linkedin" in c.get("domain", "").lower()]
        if not linkedin:
            return None
        allowed = {"name", "value", "domain", "path", "expires", "httpOnly", "secure", "sameSite"}
        sanitized = []
        samesite_map = {
            "no_restriction": "None", "unspecified": "Lax",
            "none": "None", "lax": "Lax", "strict": "Strict",
        }
        for c in linkedin:
            c = {k: v for k, v in c.items() if k in allowed and v is not None}
            ss = c.get("sameSite", "")
            if ss and ss.lower() in samesite_map:
                c["sameSite"] = samesite_map[ss.lower()]
            elif not ss or ss.lower() not in ("lax", "strict", "none"):
                c["sameSite"] = "Lax"
            sanitized.append(c)
        return sanitized
    except Exception as e:
        logger.warning(f"Cookie load error for user {user_id}: {e}")
        return None


def _extract_posts_from_dom(html: str) -> list[dict]:
    from scrapling.parser import Selector
    posts = []
    if not html:
        return posts
    sel = Selector(content=html)
    items = sel.css('div[role="listitem"]')
    if not items or len(items) == 0:
        items = sel.css(
            "div.feed-shared-update-v2, li.search-result, article.search-result"
        )
    for item in items:
        try:
            text = item.get_all_text(strip=True)
            if not text or len(text) < 30:
                continue
            profile_link = ""
            for pattern in ("/in/", "/company/", "/school/", "/showcase/"):
                link_el = item.css(f'a[href*="{pattern}"]').first
                if link_el:
                    href = link_el.attrib.get("href", "")
                    if href.startswith("//"):
                        href = "https:" + href
                    elif href.startswith("/"):
                        href = "https://www.linkedin.com" + href
                    profile_link = href
                    break
            if not profile_link:
                any_link = item.css('a[href*="linkedin.com"]').first
                if any_link:
                    href = any_link.attrib.get("href", "")
                    profile_link = href if href.startswith("http") else ""

            author_name = "LinkedIn User"
            if profile_link:
                name_tag = item.css('span[dir="ltr"]').first
                if name_tag:
                    name_text = name_tag.get_all_text(strip=True)
                    if name_text and len(name_text) < 60:
                        author_name = name_text

            posts.append({
                "author_name": author_name,
                "author_profile": profile_link,
                "raw_text": text,
            })
        except Exception:
            continue
    return posts


class LinkedInSearchEngine:
    def __init__(self, user_id: str = "", timeout: int = 60000, max_retries: int = 2):
        self.user_id = user_id
        self.timeout = timeout
        self.max_retries = max_retries
        self._session = None
        self._ai_client = None
        self._warmed = False

    async def _get_ai_client(self):
        if self._ai_client is not None:
            return self._ai_client
        settings = get_settings()
        if not settings.openai_api_key:
            logger.warning("OPENAI_API_KEY not set — AI features disabled")
            return None
        try:
            from openai import OpenAI
            self._ai_client = OpenAI(api_key=settings.openai_api_key)
            return self._ai_client
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAI client: {e}")
            return None

    async def _get_session(self):
        from scrapling.fetchers.stealth_chrome import AsyncStealthySession
        if self._session is None:
            cookies = _load_session_cookies(self.user_id)
            self._session = AsyncStealthySession(
                headless=True,
                block_ads=True,
                disable_resources=True,
                cookies=cookies,
                timeout=self.timeout,
                solve_cloudflare=True,
            )
            await self._session.start()
        return self._session

    def _build_url(self, keyword: str, time_filter: str) -> str:
        tf = TIME_FILTER_MAP.get(time_filter, TIME_FILTER_MAP["latest"])
        return LINKEDIN_SEARCH_URL.format(
            keyword=quote(keyword), time_filter=tf
        )

    async def generate_queries(self, topic: str, lead_type: str = "all") -> list[str]:
        client = await self._get_ai_client()
        if not client:
            return [topic] * 10
        prompt = LEAD_TYPE_PROMPTS.get(lead_type, LEAD_TYPE_PROMPTS["all"])["query"]
        try:
            loop = asyncio.get_event_loop()
            resp = await loop.run_in_executor(
                None,
                lambda: client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": f"Generate 10 intent-based LinkedIn search queries for: {topic}"},
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.7,
                ),
            )
            result = json.loads(resp.choices[0].message.content)

            if isinstance(result, list):
                queries = result
            elif isinstance(result, dict):
                queries = result.get("queries", result.get("results", []))
            else:
                queries = []
            queries = [str(q).strip() for q in queries if q and str(q).strip()]
            seen = set()
            unique = []
            for q in queries:
                key = q.lower().strip()
                if key not in seen:
                    seen.add(key)
                    unique.append(q)
                    if len(unique) == 10:
                        break
            if unique:
                return unique
        except Exception as e:
            logger.warning(f"Query generation error: {e}")
        return [topic] * 10

    async def scrape_query(self, query: str, time_filter: str) -> list[dict] | None:
        url = self._build_url(query, time_filter)
        for attempt in range(self.max_retries):
            try:
                session = await self._get_session()
                collected_urls = []

                async def page_action(page, html=None):
                    try:
                        urls = await page.evaluate(r"""() => {
                            const results = [];
                            const seen = new Set();
                            const walker = document.createTreeWalker(document.body, 1, null, false);
                            while (walker.nextNode()) {
                                const el = walker.currentNode;
                                const attr = el.getAttribute('data-urn') || el.getAttribute('data-id') || '';
                                const m = attr.match(/urn:li:activity:(\d+)/);
                                if (m && !seen.has(m[0])) {
                                    seen.add(m[0]);
                                    results.push('https://www.linkedin.com/feed/update/' + m[0] + '/');
                                }
                            }
                            return results;
                        }""")
                        collected_urls.extend(urls if isinstance(urls, list) else [])
                    except Exception:
                        pass

                result = await session.fetch(
                    url,
                    load_dom=True,
                    network_idle=False,
                    wait=8000,
                    page_action=page_action,
                )

                if not result or result.status >= 400:
                    await asyncio.sleep(2)
                    continue

                final_url = result.url.lower() if hasattr(result, 'url') else ""
                if any(x in final_url for x in ("login", "/auth/", "/checkpoint/", "challenge")):
                    await self._cleanup()
                    return None

                html = (
                    result.html_content
                    if hasattr(result, 'html_content')
                    else result.body.decode()
                )

                raw = _extract_posts_from_dom(html)
                for i, rp in enumerate(raw):
                    if i < len(collected_urls) and collected_urls[i]:
                        rp["post_url"] = collected_urls[i]
                    else:
                        rp["post_url"] = ""
                return raw

            except Exception as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"LinkedIn scrape attempt {attempt + 1} failed: {e}")
                    await asyncio.sleep(3)
                else:
                    logger.error(f"LinkedIn scrape failed after {self.max_retries} attempts: {e}", exc_info=True)
                    return None
        return []

    async def ai_extract(
        self, raw_posts: list[dict], query: str, lead_type: str = "all"
    ) -> list[dict]:
        client = await self._get_ai_client()
        if not raw_posts:
            return []
        if not client:
            return [
                {
                    "keyword": query,
                    "post_url": p.get("post_url", ""),
                    "post_text": p.get("raw_text", "")[:1000],
                    "author_name": p.get("author_name", "LinkedIn User"),
                    "author_profile": p.get("author_profile", ""),
                    "intent_score": 0.3,
                    "intent_reason": "raw post",
                    "source": "linkedin",
                }
                for p in raw_posts[:20]
            ]

        prompt = LEAD_TYPE_PROMPTS.get(lead_type, LEAD_TYPE_PROMPTS["all"])["extract"]
        all_leads = []
        batch_size = 10
        sem = asyncio.Semaphore(3)

        async def process_batch(batch: list[dict]) -> list[dict]:
            async with sem:
                texts = "\n---\n".join(
                    f"POST {i+1}: {p.get('raw_text', '')[:2000]}"
                    for i, p in enumerate(batch)
                )
                try:
                    loop = asyncio.get_event_loop()
                    resp = await loop.run_in_executor(
                        None,
                        lambda: client.chat.completions.create(
                            model="gpt-4o",
                            messages=[
                                {"role": "system", "content": prompt},
                                {
                                    "role": "user",
                                    "content": f"Find leads in these posts related to '{query}':\n\n{texts}",
                                },
                            ],
                            response_format={"type": "json_object"},
                            temperature=0.1,
                        ),
                    )
                    content = resp.choices[0].message.content

                    result = json.loads(content)
                    items = []
                    if isinstance(result, list):
                        items = result
                    elif isinstance(result, dict):
                        items = result.get("leads", result.get("results", [result]))
                    if isinstance(items, dict):
                        items = [items]
                    results = []
                    for item in items:
                        if isinstance(item, dict) and item.get("post_text"):
                            text = item["post_text"]
                            confidence = float(item.get("confidence", 0.5))
                            qualified = item.get("qualified", True)
                            score = confidence if qualified else max(0.1, confidence * 0.5)
                            if _is_provider(text):
                                score = 0
                            if score > 0.1:
                                results.append({
                                    "author_name": item.get("author_name", "LinkedIn User"),
                                    "post_text": text[:2000],
                                    "score": score,
                                    "reason": item.get("reason", ""),
                                })
                    return results
                except Exception as e:
                    logger.warning(f"Batch AI extract error: {e}")
                    return []

        tasks = [
            process_batch(raw_posts[i : i + batch_size])
            for i in range(0, len(raw_posts), batch_size)
        ]
        batch_results = await asyncio.gather(*tasks)
        scored = []
        for br in batch_results:
            scored.extend(br)

        for s in scored:
            name = s["author_name"].lower().strip()
            matched = None
            for rp in raw_posts:
                rp_name = rp.get("author_name", "").lower().strip()
                if rp_name and rp_name == name:
                    matched = rp
                    break
            if not matched:
                for rp in raw_posts:
                    if s["post_text"][:50].lower() in rp.get("raw_text", "").lower():
                        matched = rp
                        break
            all_leads.append({
                "keyword": query,
                "post_url": matched.get("post_url", "") if matched else "",
                "post_text": s["post_text"],
                "author_name": s["author_name"],
                "author_profile": matched.get("author_profile", "") if matched else "",
                "intent_score": round(s["score"], 2),
                "intent_reason": s["reason"],
                "source": "linkedin",
            })

        if not all_leads:
            for rp in raw_posts[:20]:
                all_leads.append({
                    "keyword": query,
                    "post_url": rp.get("post_url", ""),
                    "post_text": rp.get("raw_text", "")[:1000],
                    "author_name": rp.get("author_name", "LinkedIn User"),
                    "author_profile": rp.get("author_profile", ""),
                    "intent_score": 0.3,
                    "intent_reason": "raw post",
                    "source": "linkedin",
                })

        all_leads.sort(key=lambda x: x["intent_score"], reverse=True)
        return all_leads

    async def start_search(
        self, topic: str, time_filter: str = "latest", lead_type: str = "all"
    ) -> dict:
        queries = await self.generate_queries(topic, lead_type)
        raw = await self.scrape_query(queries[0], time_filter)
        if raw is None:
            logger.warning(f"LinkedIn scraper failed for topic '{topic}' — session may be invalid")
            return {"leads": [], "has_more": False, "session_valid": False}
        if not raw:
            logger.info(f"LinkedIn scrape returned 0 posts for query '{queries[0]}' — no matching results found")
            return {"leads": [], "has_more": False, "session_valid": True, "all_leads": []}
        logger.info(f"LinkedIn scrape found {len(raw)} raw posts for query '{queries[0]}', running AI extraction...")
        leads = await self.ai_extract(raw, queries[0], lead_type)
        logger.info(f"AI extraction returned {len(leads)} qualified leads out of {len(raw)} raw posts")
        return {
            "leads": leads[:10],
            "has_more": len(leads) > 10 or len(queries) > 1,
            "session_valid": True,
            "lead_type": lead_type,
            "all_leads": leads,
        }

    async def load_more(self, prev_leads: list[dict], all_leads: list[dict]) -> dict:
        remaining = all_leads[len(prev_leads):]
        if remaining:
            return {"leads": remaining[:10], "has_more": len(remaining) > 10}
        return {"leads": [], "has_more": False}

    async def save_leads(
        self, search_id: str, user_id: str, leads: list[dict]
    ) -> list[str]:
        supabase = get_supabase_admin()
        saved_ids = []
        for lead in leads:
            try:
                author_name = lead.get("author_name", "LinkedIn User")
                lead_data = {
                    "search_id": search_id,
                    "user_id": user_id,
                    "source": "linkedin",
                    "business_name": author_name,
                    "author_name": author_name,
                    "author_profile": lead.get("author_profile", ""),
                    "post_text": lead.get("post_text", ""),
                    "post_url": lead.get("post_url", ""),
                    "intent_score": lead.get("intent_score", 0),
                    "intent_reason": lead.get("intent_reason", ""),
                    "linkedin_keyword": lead.get("keyword", ""),
                    "lead_category": "hot" if lead.get("intent_score", 0) >= 0.7 else "warm",
                }
                response = await asyncio.to_thread(
                    lambda: supabase.table("leads").insert(lead_data).execute()
                )
                if response.data:
                    saved_ids.append(response.data[0]["id"])
            except Exception as e:
                logger.error(f"Failed to save LinkedIn lead: {e}")
        return saved_ids

    async def _cleanup(self):
        if self._session:
            try:
                await self._session.close()
            except Exception:
                pass
            self._session = None

    async def warmup(self):
        if self._warmed:
            return
        try:
            session = await self._get_session()
            await session.fetch(
                "https://www.linkedin.com",
                load_dom=False,
                network_idle=False,
                wait=500,
            )
            self._warmed = True
        except Exception as e:
            logger.warning(f"LinkedIn warmup failed for user {self.user_id}: {e}")
