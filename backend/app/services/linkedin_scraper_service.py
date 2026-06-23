import asyncio
import json
import logging
import re
from urllib.parse import quote

from app.config import get_settings
from app.database import get_supabase_admin

from app.services.linkedin_auth_service import LinkedInSessionManager

logger = logging.getLogger(__name__)

TIME_FILTER_MAP = {
    "latest": "past-24h",
    "7_days": "past-week",
    "14_days": "past-two-weeks",
    "27_days": "r2592000",
    "2_months": "r4838400",
}

LINKEDIN_SEARCH_URL = (
    "https://www.linkedin.com/search/results/content/"
    "?keywords={keyword}&sortBy=date&datePosted={time_filter}"
)

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


POST_EXTRACTION_JS = """
() => {
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
        const textSelectors = [
            '.update-components-text',
            '.feed-shared-update-v2__description',
            '.feed-shared-text',
            '.break-words',
        ];
        for (const sel of textSelectors) {
            const textEl = el.querySelector(sel);
            if (textEl) {
                const t = textEl.innerText?.trim() || '';
                if (t.length > text.length && t.length > 20) text = t;
            }
        }

        if (!text || text.length < 20) {
            const allDivs = el.querySelectorAll('div, span');
            let maxLen = 0;
            allDivs.forEach(div => {
                const t = div.innerText?.trim() || '';
                if (t.length > maxLen && t.length > 50 &&
                    !t.includes('followers') && !t.match(/^\\d+[hdwmy]\\s/)) {
                    const parent = div.parentElement;
                    if (parent && !parent.classList.contains('feed-shared-actor')) {
                        text = t; maxLen = t.length;
                    }
                }
            });
        }

        if (!text || text.length < 20) continue;

        const authorEl = el.querySelector(
            '[class*="actor__name"], [class*="update-components-actor__name"], [class*="hoverable-link-text"]'
        );
        const author = authorEl ? authorEl.innerText.trim() : '';

        const timeEl = el.querySelector(
            '[class*="actor__sub-description"], [class*="update-components-actor__sub-description"]'
        );
        const timeText = timeEl ? timeEl.innerText.split('•')[0].trim() : '';

        const reactEl = el.querySelector(
            'button[aria-label*="reaction"], [class*="social-details-social-counts__reactions"]'
        );
        const reactions = reactEl ? reactEl.innerText.trim() : '';

        const commEl = el.querySelector('button[aria-label*="comment"]');
        const comments = commEl ? commEl.innerText.trim() : '';

        const profileLink = '';
        const linkEl = el.querySelector('a[href*="/in/"], a[href*="/company/"]');
        if (linkEl) {
            let href = linkEl.getAttribute('href') || '';
            if (href.startsWith('//')) href = 'https:' + href;
            else if (href.startsWith('/')) href = 'https://www.linkedin.com' + href;
        }

        posts.push({
            urn: fullUrn,
            author: author,
            text: text.substring(0, 2000),
            timeText: timeText,
            reactions: reactions,
            comments: comments,
            profileLink: profileLink,
        });
    }
    return posts;
}
"""


class LinkedInSearchEngine:
    def __init__(self, user_id: str = "", timeout: int = 60000, max_retries: int = 2):
        self.user_id = user_id
        self.timeout = timeout
        self.max_retries = max_retries
        self._session = None
        self._ai_client = None
        self._session_mgr = LinkedInSessionManager(user_id=user_id)

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

    async def _ensure_browser(self) -> bool:
        if self._session is not None:
            return True

        cookies = self._session_mgr.load_cookies()
        if not cookies:
            logger.warning(f"No LinkedIn cookies found for user {self.user_id}")
            return False

        has_li_at = any(c.get("name") == "li_at" for c in cookies)
        if not has_li_at:
            logger.warning("No li_at cookie found")
            return False

        try:
            from scrapling.fetchers import AsyncStealthySession

            self._session = AsyncStealthySession(
                headless=True,
                solve_cloudflare=True,
                block_webrtc=True,
                hide_canvas=True,
                timeout=self.timeout,
                cookies=cookies,
            )
            await self._session.__aenter__()

            resp = await self._session.fetch(
                "https://www.linkedin.com/feed/",
                load_dom=True,
                timeout=30000,
            )

            final_url = resp.url.lower()
            if any(x in final_url for x in ("login", "/auth/", "/checkpoint/", "challenge", "signup")):
                logger.warning("LinkedIn session invalid after cookie import")
                await self._cleanup()
                return False

            logger.info("LinkedIn browser ready with valid session (Scrapling StealthyFetcher)")
            return True
        except Exception as e:
            logger.error(f"Failed to start LinkedIn stealth browser: {e}")
            await self._cleanup()
            return False

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
        ok = await self._ensure_browser()
        if not ok:
            return None

        url = self._build_url(query, time_filter)

        for attempt in range(self.max_retries):
            try:
                extracted_posts = []

                async def scroll_and_extract(page):
                    for _ in range(5):
                        try:
                            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                            await asyncio.sleep(1.5)
                        except Exception:
                            break

                    try:
                        posts = await page.evaluate(POST_EXTRACTION_JS)
                        if posts and isinstance(posts, list):
                            extracted_posts.extend(posts)
                    except Exception as e:
                        logger.warning(f"JS extraction error: {e}")

                resp = await self._session.fetch(
                    url,
                    network_idle=True,
                    load_dom=True,
                    page_action=scroll_and_extract,
                    solve_cloudflare=True,
                    timeout=self.timeout,
                )

                final_url = resp.url.lower()
                if any(x in final_url for x in ("login", "/auth/", "/checkpoint/", "challenge", "signup")):
                    logger.warning("Session invalid during scrape")
                    await self._cleanup()
                    return None

                if extracted_posts:
                    logger.info(f"JS extracted {len(extracted_posts)} posts for query '{query}'")
                    return extracted_posts

                html = resp.content.decode("utf-8", errors="replace")
                posts_from_html = self._extract_posts_from_html(html)
                if posts_from_html:
                    logger.info(f"HTML extracted {len(posts_from_html)} posts for query '{query}'")
                    return posts_from_html

                logger.info(f"Query '{query}' with filter '{time_filter}' returned 0 posts")
                return []

            except asyncio.TimeoutError:
                logger.warning(f"LinkedIn fetch timed out for query '{query}' (attempt {attempt + 1})")
                if attempt < self.max_retries - 1:
                    continue
                return None
            except Exception as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"LinkedIn scrape attempt {attempt + 1} failed: {e}")
                    await asyncio.sleep(3)
                else:
                    logger.error(f"LinkedIn scrape failed after {self.max_retries} attempts: {e}")
                    return None
        return []

    def _extract_posts_from_html(self, html: str) -> list[dict]:
        posts = []
        urns = set(re.findall(r'data-urn="(urn:li:activity:\d+)"', html))
        if not urns:
            urns = set(re.findall(r'urn:li:activity:(\d+)', html))
            urns = {f"urn:li:activity:{u}" for u in urns}

        for urn in urns:
            try:
                activity_id = urn.replace("urn:li:activity:", "")
                post_url = f"https://www.linkedin.com/feed/update/urn:li:activity:{activity_id}/"

                name_match = re.search(
                    r'class="[^"]*actor__name[^"]*"[^>]*>([^<]+)',
                    html[html.find(urn) - 2000:html.find(urn) + 2000]
                    if urn in html else html,
                )
                author = name_match.group(1).strip() if name_match else "LinkedIn User"

                text_match = re.search(
                    r'class="[^"]*update-components-text[^"]*"[^>]*>(.*?)</div>',
                    html[html.find(urn) - 1000:html.find(urn) + 3000]
                    if urn in html else html,
                    re.DOTALL,
                )
                text = ""
                if text_match:
                    text = re.sub(r'<[^>]+>', '', text_match.group(1)).strip()
                    text = text[:2000]

                if not text or len(text) < 20:
                    continue

                posts.append({
                    "author_name": author,
                    "post_url": post_url,
                    "raw_text": text,
                })
            except Exception:
                continue

        return posts

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
                    "post_text": p.get("text", p.get("raw_text", ""))[:1000],
                    "author_name": p.get("author", p.get("author_name", "LinkedIn User")),
                    "author_profile": p.get("profileLink", p.get("author_profile", "")),
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
                    f"POST {i+1}: {(p.get('text', p.get('raw_text', '')) or '')[:2000]}"
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
                rp_name = (rp.get("author", rp.get("author_name", "")) or "").lower().strip()
                if rp_name and rp_name == name:
                    matched = rp
                    break
            if not matched:
                for rp in raw_posts:
                    text_to_check = rp.get("text", rp.get("raw_text", "")) or ""
                    if s["post_text"][:50].lower() in text_to_check.lower():
                        matched = rp
                        break
            all_leads.append({
                "keyword": query,
                "post_url": matched.get("post_url", "") if matched else "",
                "post_text": s["post_text"],
                "author_name": s["author_name"],
                "author_profile": matched.get("profileLink", matched.get("author_profile", "")) if matched else "",
                "intent_score": round(s["score"], 2),
                "intent_reason": s["reason"],
                "source": "linkedin",
            })

        if not all_leads:
            for rp in raw_posts[:20]:
                all_leads.append({
                    "keyword": query,
                    "post_url": rp.get("post_url", ""),
                    "post_text": (rp.get("text", rp.get("raw_text", "")) or "")[:1000],
                    "author_name": rp.get("author", rp.get("author_name", "LinkedIn User")),
                    "author_profile": rp.get("profileLink", rp.get("author_profile", "")),
                    "intent_score": 0.3,
                    "intent_reason": "raw post",
                    "source": "linkedin",
                })

        all_leads.sort(key=lambda x: x["intent_score"], reverse=True)
        return all_leads

    async def start_search(
        self, topic: str, time_filter: str = "latest", lead_type: str = "all"
    ) -> dict:
        try:
            return await asyncio.wait_for(
                self._start_search_internal(topic, time_filter, lead_type),
                timeout=300,
            )
        except asyncio.TimeoutError:
            logger.error(f"LinkedIn search timed out for topic '{topic}' after 300s")
            await self._cleanup()
            return {"leads": [], "has_more": False, "session_valid": False, "timeout": True}

    async def _start_search_internal(
        self, topic: str, time_filter: str = "latest", lead_type: str = "all"
    ) -> dict:
        ok = await self.verify_session()
        if not ok:
            logger.warning("LinkedIn session invalid — skipping search")
            return {"leads": [], "has_more": False, "session_valid": False}
        queries = await self.generate_queries(topic, lead_type)
        all_qualified: list[dict] = []
        seen_authors: set[str] = set()
        MIN_TARGET = 10
        TIME_FILTERS = ["latest", "7_days", "14_days", "27_days", "2_months"]

        for i, query in enumerate(queries[:5]):
            if len(all_qualified) >= MIN_TARGET:
                break
            for tf in TIME_FILTERS:
                if len(all_qualified) >= MIN_TARGET:
                    break
                raw = await self.scrape_query(query, tf)
                if raw is None:
                    logger.warning(f"LinkedIn scraper failed on query '{query}' ({tf}) — session invalid or no cookies")
                    return {"leads": [], "has_more": False, "session_valid": False}
                if not raw:
                    logger.info(f"Query '{query}' with filter '{tf}' returned 0 posts")
                    continue
                logger.info(f"Query {i+1} '{query}' ({tf}): {len(raw)} raw posts")
                leads = await self.ai_extract(raw, query, lead_type)
                for lead in leads:
                    author = lead.get("author_name", "").lower().strip()
                    if author and author not in seen_authors:
                        seen_authors.add(author)
                        all_qualified.append(lead)
                logger.info(f"Query {i+1} '{query}' ({tf}): {len(leads)} qualified (total unique: {len(all_qualified)})")

        logger.info(f"LinkedIn search complete: {len(all_qualified)} unique qualified leads from topic '{topic}'")
        return {
            "leads": all_qualified[:10],
            "has_more": len(all_qualified) > 10,
            "session_valid": True,
            "lead_type": lead_type,
            "all_leads": all_qualified,
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
        if self._session is not None:
            try:
                await self._session.close()
            except Exception:
                pass
            self._session = None

    async def verify_session(self) -> bool:
        cookies = self._session_mgr.load_cookies()
        if not cookies:
            return False
        try:
            import httpx
            cookie_str = "; ".join(f"{c['name']}={c['value']}" for c in cookies if c.get("name") and c.get("value"))
            async with httpx.AsyncClient(timeout=10, follow_redirects=False) as client:
                resp = await client.get(
                    "https://www.linkedin.com/feed/",
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
                        "Cookie": cookie_str,
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    },
                )
                if resp.status_code in (302, 303, 307):
                    loc = resp.headers.get("location", "")
                    if any(x in loc.lower() for x in ("login", "/auth/", "signup")):
                        logger.warning("LinkedIn session expired — redirected to login")
                        return False
                    return True
                if resp.status_code < 400:
                    logger.info("LinkedIn session verified — cookies are valid")
                    return True
                logger.warning(f"LinkedIn session check returned {resp.status_code}")
                return False
        except Exception as e:
            logger.warning(f"LinkedIn session verify failed (httpx), falling back to browser: {e}")
            return False

    async def warmup(self):
        pass
