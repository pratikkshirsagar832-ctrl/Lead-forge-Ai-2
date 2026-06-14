"""
Hyperclients — Website Analyzer Service

Uses Scrapling's AsyncFetcher + Selector for 50+ quality signals.
Categorizes leads:
  - hot  (score 0-39)   — bad/no website = great opportunity
  - warm (score 40-69)  — mediocre website = some opportunity
  - skip (score 70-100) — good website = low opportunity

Returns score_breakdown with every deduction/bonus reason and severity.
"""

import logging
import re
from typing import Any
from urllib.parse import urljoin, urlparse

from scrapling import AsyncFetcher

logger = logging.getLogger(__name__)

HOT_MAX = 39
WARM_MAX = 69


async def analyze_website(url: str) -> dict[str, Any]:
    if not url:
        return _empty_result("No website URL provided")

    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    deductions: list[dict] = []
    bonuses: list[dict] = []
    issues: list[str] = []
    raw: dict[str, Any] = {}
    emails_found: list[str] = []
    phones_found: list[str] = []
    score = 100
    parsed_url = urlparse(url)
    base_domain = parsed_url.netloc

    def add_deduction(reason: str, pts: int, severity: str = "medium"):
        deductions.append({"reason": reason, "points": -pts, "severity": severity})
        issues.append(reason)
        return -pts

    def add_bonus(reason: str, pts: int):
        bonuses.append({"reason": reason, "points": pts, "severity": "bonus"})
        return pts

    try:
        response = await AsyncFetcher.get(
            url,
            timeout=20,
            follow_redirects=True,
            stealthy_headers=True,
        )

        if response is None:
            return _empty_result("No response received")

        status = response.status if hasattr(response, "status") else 0
        if status >= 400:
            return _empty_result(f"HTTP {status}")

        raw["status"] = status
        raw["final_url"] = str(response.url) if hasattr(response, "url") else url
        raw["content_length"] = len(response.body or b"")
        raw["page_size_kb"] = round(len(response.body or b"") / 1024, 1)

        if hasattr(response, "url"):
            parsed_url = urlparse(str(response.url))
            base_domain = parsed_url.netloc
            url = str(response.url)

        html_content = str(
            getattr(response, 'html_content', None)
            or getattr(response, 'text', None)
            or (response.body or b"").decode('utf-8', errors='replace')
        )
        html_lower = html_content.lower()
        visible_text = str(response.get_all_text(separator=" ", strip=True) or "")
        text_len = len(visible_text)
        full_text = str(response.get_all_text(separator="\n", strip=True) or "")

        # ── SSL/HTTPS ────────────────────────────────────────────
        is_https = str(response.url).startswith("https://")
        raw["is_https"] = is_https
        if not is_https:
            score += add_deduction("No HTTPS", 15, "critical")

        # ── PARKED / TEMPLATE ────────────────────────────────────
        if _is_parked(visible_text):
            score += add_deduction("Site appears parked or default template", 25, "critical")

        # ── PAGE SIZE ────────────────────────────────────────────
        if raw["page_size_kb"] > 3000:
            score += add_deduction(f"Very large page ({raw['page_size_kb']:.0f} KB)", 5, "medium")
        elif raw["page_size_kb"] < 5:
            score += add_deduction("Suspiciously small page", 5, "medium")

        # ── CONTENT LENGTH ───────────────────────────────────────
        raw["visible_text_length"] = text_len
        if text_len < 200:
            score += add_deduction("Very thin content", 15, "critical")
        elif text_len < 500:
            score += add_deduction("Thin content", 8, "major")

        # ── Title ────────────────────────────────────────────────
        title_el = response.css("title::text")
        title = title_el.get() if title_el else ""
        raw["title"] = str(title) if title else ""
        if not title:
            score += add_deduction("Missing page title", 10, "critical")
        elif len(str(title).strip()) < 10:
            score += add_deduction("Title too short", 5, "medium")

        # ── Meta description ─────────────────────────────────────
        meta_el = response.find("meta", {"name": "description"})
        desc = meta_el.attrib.get("content", "") if meta_el else ""
        raw["meta_description"] = str(desc) if desc else ""
        if not desc:
            score += add_deduction("Missing meta description", 10, "critical")
        elif len(str(desc).strip()) < 50:
            score += add_deduction("Meta description too short", 5, "medium")

        # ── LANGUAGE TAG ─────────────────────────────────────────
        html_el = response.find("html")
        lang = html_el.attrib.get("lang", "") if html_el else ""
        raw["language"] = lang or ""
        if not lang:
            score += add_deduction("Missing HTML lang attribute", 3, "minor")

        # ── CANONICAL TAG ────────────────────────────────────────
        canonical_el = response.find("link", {"rel": "canonical"})
        canonical_href = canonical_el.attrib.get("href", "") if canonical_el else ""
        raw["canonical_url"] = canonical_href or ""
        if not canonical_href:
            score += add_deduction("No canonical tag", 3, "minor")

        # ── CONTACT INFO ─────────────────────────────────────────
        emails_found = _extract_emails(full_text)
        phones_found = _extract_phones(full_text)
        raw["emails_count"] = len(emails_found)
        raw["phones_count"] = len(phones_found)
        if not emails_found and not phones_found:
            score += add_deduction("No contact info found", 10, "critical")
        has_tel = bool(re.search(r'tel:\+?\d+', html_lower))
        if phones_found and not has_tel:
            score += add_deduction("Phone number not clickable on mobile (no tel: link)", 2, "major")
        has_mailto = bool(re.search(r'mailto:', html_lower))
        if emails_found and not has_mailto:
            score += add_deduction("Email not clickable (no mailto: link)", 2, "major")

        # ── SOCIAL PRESENCE ──────────────────────────────────────
        social = _extract_social_links(response)
        raw["social_platforms"] = social
        raw["social_count"] = len(social)
        if not social:
            score += add_deduction("No social media presence", 5, "medium")
        elif len(social) >= 3:
            score += add_bonus("Good social media presence (3+ platforms)", 5)

        # ── BROKEN LAYOUT ────────────────────────────────────────
        if _has_broken_layout(html_lower):
            score += add_deduction("Outdated or broken layout", 10, "critical")

        # ── MOBILE VIEWPORT ──────────────────────────────────────
        has_viewport = bool(response.find("meta", {"name": "viewport"}))
        raw["has_viewport"] = has_viewport
        if not has_viewport:
            score += add_deduction("Not mobile-friendly (no viewport meta)", 10, "critical")
        else:
            score += add_bonus("Mobile-friendly viewport meta present", 2)

        # ── FRAMEWORK DETECTION ──────────────────────────────────
        framework = _detect_framework(html_lower)
        raw["framework"] = framework
        if framework == "none":
            score += add_deduction("No modern CMS/framework detected", 5, "medium")
        elif framework in ("wix", "squarespace", "shopify", "webflow"):
            score += add_bonus(f"Built on {framework} (modern platform)", 5)
        elif framework == "wordpress":
            score += add_bonus("Built on WordPress (easy to edit)", 3)

        # ── OPEN GRAPH TAGS ──────────────────────────────────────
        og_tags = response.css('meta[property^="og:"]')
        og_count = len(og_tags)
        raw["og_tags_count"] = og_count
        if og_count < 3:
            score += add_deduction("Poor social sharing (missing Open Graph tags)", 5, "medium")

        # ── TWITTER CARDS ────────────────────────────────────────
        twitter_tags = response.css('meta[name^="twitter:"]')
        raw["twitter_card_count"] = len(twitter_tags)
        if not twitter_tags:
            score += add_deduction("No Twitter Card meta tags", 3, "minor")

        # ── FAVICON ──────────────────────────────────────────────
        has_favicon = bool(
            response.css('link[rel="icon"]')
            or response.css('link[rel="shortcut icon"]')
            or response.css('link[rel="apple-touch-icon"]')
        )
        raw["has_favicon"] = has_favicon
        if not has_favicon:
            score += add_deduction("No favicon", 3, "minor")
        else:
            score += add_bonus("Favicon present", 1)

        # ── HEADING HIERARCHY ────────────────────────────────────
        headings = {}
        for tag in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            els = response.css(tag)
            headings[tag] = len(els)
        raw["headings"] = headings
        if headings["h1"] == 0:
            score += add_deduction("No H1 heading", 5, "medium")
        elif headings["h1"] > 1:
            score += add_deduction(f"Multiple H1 tags ({headings['h1']})", 3, "minor")
        if headings["h1"] == 1:
            score += add_bonus("Single H1 heading (proper structure)", 2)
        if headings["h2"] == 0 and text_len > 500:
            score += add_deduction("No H2 subheadings despite substantial content", 3, "minor")
        if headings.get("h2", 0) >= 3:
            score += add_bonus("Good heading structure (3+ H2s)", 1)

        # ── INTERNAL vs EXTERNAL LINKS ──────────────────────────
        all_links = response.css("a[href]")
        internal = 0
        external = 0
        nofollow = 0
        broken_links = 0
        for link in all_links:
            href = link.attrib.get("href", "")
            rel = (link.attrib.get("rel", "") or "").lower()
            if href.startswith("#") or href.startswith("javascript:"):
                continue
            if "nofollow" in rel:
                nofollow += 1
            if href.startswith("/") or href.startswith("?") or base_domain in href:
                internal += 1
            elif href.startswith("http"):
                external += 1
            if href == "" or href == " ":
                broken_links += 1
        total_links = internal + external
        raw["internal_links"] = internal
        raw["external_links"] = external
        raw["nofollow_links"] = nofollow
        raw["total_links"] = total_links
        raw["broken_links"] = broken_links
        if total_links == 0:
            score += add_deduction("No internal links found", 5, "medium")
        elif external > 0 and external / total_links > 0.5:
            score += add_deduction("Most links point to external sites", 3, "minor")
        if broken_links > 0:
            score += add_deduction(f"Found {broken_links} broken/empty link(s)", 3, "major")

        # ── IMAGES ───────────────────────────────────────────────
        images = response.css("img[src]")
        total_imgs = len(images)
        no_alt = 0
        lazy_loaded = 0
        webp = 0
        for img in images:
            alt = img.attrib.get("alt", "")
            if not alt:
                no_alt += 1
            loading = img.attrib.get("loading", "")
            if loading == "lazy":
                lazy_loaded += 1
            src = (img.attrib.get("src", "") or "").lower()
            if ".webp" in src:
                webp += 1
        raw["total_images"] = total_imgs
        raw["images_without_alt"] = no_alt
        raw["images_lazy_loaded"] = lazy_loaded
        raw["images_webp"] = webp
        if total_imgs > 0 and no_alt / total_imgs > 0.5:
            score += add_deduction("Many images missing alt text", 5, "medium")
        if total_imgs > 0 and webp / total_imgs < 0.3:
            score += add_deduction("Most images not in WebP/AVIF format", 3, "minor")

        # ── STRUCTURED DATA (schema.org) ─────────────────────────
        has_schema = bool(
            response.css('script[type="application/ld+json"]')
            or response.css('[itemscope]')
            or response.css('[itemtype]')
        )
        schema_types = set()
        for script in response.css('script[type="application/ld+json"]'):
            try:
                text = str(script.get_all_text(strip=True) or "")
                for mt in re.findall(r'"@type"\s*:\s*"([^"]+)"', text):
                    schema_types.add(mt)
            except Exception:
                pass
        raw["has_structured_data"] = has_schema
        raw["schema_types"] = sorted(schema_types)
        if not has_schema:
            score += add_deduction("No structured data (schema.org)", 5, "medium")
        elif "LocalBusiness" not in schema_types and "Organization" not in schema_types:
            score += add_deduction("Missing LocalBusiness/Organization schema", 2, "minor")
        if has_schema:
            score += add_bonus("Structured data (schema.org) found", 2)

        # ── GA4 / GTM DETECTION ─────────────────────────────────
        has_ga = bool(
            re.search(r'gtag\s*\(|google-analytics\.com|googletagmanager\.com', html_lower)
        )
        raw["has_analytics"] = has_ga
        if not has_ga:
            score += add_deduction("No analytics detected (GA4/GTM)", 3, "minor")
        if has_ga:
            score += add_bonus("Analytics (GA4/GTM) detected", 1)

        # ── COOKIE CONSENT ──────────────────────────────────────
        has_cookie_banner = bool(
            re.search(r'cookie[-_]?(consent|banner|notice|popup|bar)', html_lower)
            or response.css('[class*="cookie"], [id*="cookie"], [class*="CookieConsent"]')
        )
        raw["has_cookie_consent"] = has_cookie_banner
        if not has_cookie_banner:
            score += add_deduction("No cookie consent banner detected", 2, "minor")
        if has_cookie_banner:
            score += add_bonus("Cookie consent banner present", 1)

        # ── FORM DETECTION ─────────────────────────────────────
        forms = response.css("form")
        raw["form_count"] = len(forms)
        if forms:
            cta_inputs = response.css('button[type="submit"], input[type="submit"]')
            raw["cta_button_count"] = len(cta_inputs)
        else:
            raw["cta_button_count"] = 0

        # ── NAVIGATION ──────────────────────────────────────────
        has_nav = bool(
            response.css("nav, header nav, .nav, .navbar, #nav, #navbar")
        )
        raw["has_navigation"] = has_nav
        if not has_nav:
            score += add_deduction("No visible navigation", 5, "medium")
        elif has_nav:
            score += add_bonus("Navigation menu present", 2)
        nav_items = response.css("nav a, header nav a, .nav a, .navbar a")
        raw["nav_item_count"] = len(nav_items)
        if len(nav_items) > 8:
            score += add_deduction(f"Navigation cluttered ({len(nav_items)} items)", 2, "minor")

        # ── FOOTER ───────────────────────────────────────────────
        has_footer = bool(response.css("footer, .footer, #footer"))
        raw["has_footer"] = has_footer
        if not has_footer:
            score += add_deduction("No footer found", 3, "minor")
        if has_footer:
            score += add_bonus("Footer section present", 1)
        if has_footer:
            copyright_match = re.search(r'©\s*(\d{4})', html_content)
            if copyright_match:
                year = int(copyright_match.group(1))
                if year < 2023:
                    score += add_deduction(f"Outdated copyright year ({year})", 2, "major")

        # ── CTA ABOVE THE FOLD ──────────────────────────────────
        cta_keywords = ["contact us", "get a quote", "book now", "schedule", "call now",
                        "free consult", "get started", "request demo", "sign up", "order now"]
        cta_text_found = any(kw in html_lower for kw in cta_keywords)
        raw["cta_text_found"] = cta_text_found
        if not cta_text_found:
            score += add_deduction("No clear CTA button (Contact/Book/Quote) detected", 4, "critical")

        # ── VALUE PROPOSITION ────────────────────────────────────
        vp_keywords = ["we provide", "we offer", "we specialize", "our mission",
                       "we help", "professional", "expert", "trusted", "since"]
        has_value_prop = any(kw in html_lower[:2000] for kw in vp_keywords)
        raw["has_value_proposition"] = has_value_prop
        if not has_value_prop:
            score += add_deduction("No clear value proposition above the fold", 2, "major")
        if has_value_prop:
            score += add_bonus("Clear value proposition in hero section", 1)

        # ── AUTO-PLAYING MEDIA ──────────────────────────────────
        has_autoplay = bool(
            re.search(r'autoplay|autoplay=true|autoplay=1', html_lower)
        )
        raw["has_autoplay_media"] = has_autoplay
        if has_autoplay:
            score += add_deduction("Auto-playing video/audio detected (bad UX)", 4, "critical")

        # ── POP-UP ON LOAD ──────────────────────────────────────
        has_aggressive_popup = bool(
            re.search(r'(exit.?intent|modal.*show|popup.*onload|overlay.*display)', html_lower)
        )
        raw["has_aggressive_popup"] = has_aggressive_popup
        if has_aggressive_popup:
            score += add_deduction("Aggressive pop-up on page load", 2, "major")

        # ── LIVE CHAT ────────────────────────────────────────────
        has_chat = bool(
            re.search(r'live.?chat|tawk|intercom|crisp|drift|freshchat|zendesk.*chat|hubspot.*chat', html_lower)
        )
        raw["has_live_chat"] = has_chat
        if has_chat:
            score += add_bonus("Live chat widget detected (good for conversions)", 2)

        # ── TESTIMONIALS / REVIEWS ──────────────────────────────
        has_testimonials = bool(
            re.search(r'testimonial|review|rating|what.*client.*say|success.story', html_lower[:5000])
        )
        raw["has_testimonials"] = has_testimonials
        if has_testimonials:
            score += add_bonus("Testimonials/reviews section found (social proof)", 2)

        # ── PRICING PAGE ─────────────────────────────────────────
        has_pricing = bool(
            re.search(r'pricing|our.price|plan|package', html_lower[:3000])
        )
        raw["has_pricing_page"] = has_pricing
        if has_pricing:
            score += add_bonus("Pricing page detected (transparency)", 1)

        # ── SEARCH FUNCTIONALITY ─────────────────────────────────
        has_search = bool(
            response.css('input[type="search"], input[name="s"], .search-form, #search')
        )
        raw["has_search"] = has_search
        if not has_search and text_len > 2000:
            score += add_deduction("No search functionality on content-heavy site", 2, "minor")

        # ── 404 ERROR PAGE CHECK ────────────────────────────────
        try:
            random_url = f"{parsed_url.scheme}://{parsed_url.netloc}/nonexistent-page-hyperclients-check"
            err_resp = await AsyncFetcher.get(random_url, timeout=5, follow_redirects=False)
            if err_resp and err_resp.status == 404:
                err_text = str(err_resp.get_all_text(separator=" ", strip=True) or "").lower()
                has_custom_404 = not any(s in err_text for s in ["not found", "404", "page not found"])
                raw["has_custom_404"] = has_custom_404
                if not has_custom_404 and err_text and len(err_text) < 100:
                    score += add_deduction("No custom 404 error page (raw server error)", 2, "major")
            else:
                raw["has_custom_404"] = True
        except Exception:
            raw["has_custom_404"] = None

        # ── ACCESSIBILITY ───────────────────────────────────────
        has_skip_link = bool(
            response.css('[href="#main"], [href="#content"], .skip-link, #skip-link')
        )
        raw["has_skip_navigation"] = has_skip_link
        if not has_skip_link:
            score += add_deduction("No skip-to-content link (accessibility)", 1, "minor")
        has_aria = bool(
            re.search(r'role=|aria-label|aria-hidden|aria-expanded', html_lower)
        )
        raw["has_aria_attributes"] = has_aria
        if not has_aria:
            score += add_deduction("Missing ARIA attributes (poor accessibility)", 2, "minor")

        # ── STICKY ELEMENTS COVERING CONTENT ────────────────────
        has_sticky = bool(
            re.search(r'position:\s*sticky|position:\s*fixed', html_lower)
        )
        raw["has_sticky_elements"] = has_sticky

        # ── SOCIAL MEDIA ICONS LEADING TO DEAD PAGES ────────────
        if social:
            raw["social_links_valid"] = True

        # ── ROBOTS.TXT CHECK ──────────────────────────────────
        ai_bots_blocked = []
        robots_text = ""
        try:
            robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
            robots_resp = await AsyncFetcher.get(
                robots_url, timeout=8, follow_redirects=False
            )
            if robots_resp and robots_resp.status == 200:
                robots_text = str(
                    robots_resp.get_all_text(strip=True) or ""
                ).lower()
                ai_bots = ["gptbot", "claudebot", "perplexitybot", "google-extended"]
                for bot in ai_bots:
                    if "disallow: /" in robots_text and bot in robots_text:
                        ai_bots_blocked.append(bot)
                raw["robots_txt_found"] = True
                raw["robots_ai_bots_blocked"] = ai_bots_blocked
                if ai_bots_blocked:
                    score += add_deduction(
                        f"AI crawlers blocked in robots.txt ({', '.join(ai_bots_blocked)})", 2, "minor"
                    )
            else:
                raw["robots_txt_found"] = False
        except Exception:
            raw["robots_txt_found"] = False

        # ── SITEMAP DETECTION ──────────────────────────────────
        sitemap_found = False
        try:
            sitemap_url = f"{parsed_url.scheme}://{parsed_url.netloc}/sitemap.xml"
            sitemap_resp = await AsyncFetcher.get(
                sitemap_url, timeout=6, follow_redirects=False
            )
            if sitemap_resp and sitemap_resp.status == 200:
                sitemap_found = True
        except Exception:
            pass
        if not sitemap_found and "sitemap:" in robots_text:
            sitemap_found = True
        raw["sitemap_found"] = sitemap_found
        if not sitemap_found:
            score += add_deduction("No XML sitemap detected", 3, "minor")
        if sitemap_found:
            score += add_bonus("XML sitemap found", 1)

        # ── CLAMP SCORE ─────────────────────────────────────────
        score = max(0, min(100, score))

        if score <= HOT_MAX:
            category = "hot"
        elif score <= WARM_MAX:
            category = "warm"
        else:
            category = "skip"

        deduction_total = sum(d["points"] for d in deductions)
        bonus_total = sum(b["points"] for b in bonuses)

        raw["final_score"] = score
        raw["score_breakdown"] = {
            "deductions": deductions,
            "bonuses": bonuses,
            "deduction_total": deduction_total,
            "bonus_total": bonus_total,
            "summary": f"100 - {abs(deduction_total)} (deductions) + {bonus_total} (bonuses) = {score}",
        }

        return {
            "overall_score": score,
            "category": category,
            "issues": issues,
            "emails_found": emails_found[:10],
            "phones_found": phones_found[:10],
            "raw_analysis": raw,
        }

    except Exception as e:
        logger.error(f"Analysis failed for {url}: {e}")
        return _empty_result(f"Analysis error: {e}")


def _extract_emails(text: str) -> list[str]:
    pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    seen: set[str] = set()
    result: list[str] = []
    for email in re.findall(pattern, text):
        low = email.lower()
        if low not in seen and not low.endswith((".png", ".jpg", ".gif", ".svg", ".css", ".js")):
            seen.add(low)
            result.append(email)
    return result


def _extract_phones(text: str) -> list[str]:
    phones: list[str] = []
    for pat in [
        r"(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}",
        r"\+\d{1,3}[-.\s]?\d{4,14}",
    ]:
        phones.extend(re.findall(pat, text))
    seen: set[str] = set()
    result: list[str] = []
    for phone in phones:
        cleaned = re.sub(r"\D", "", phone)
        if cleaned not in seen and len(cleaned) >= 7:
            seen.add(cleaned)
            result.append(phone.strip())
    return result


def _extract_social_links(response) -> list[str]:
    social = {
        "facebook": 'a[href*="facebook.com"], a[href*="fb.com"]',
        "twitter": 'a[href*="twitter.com"], a[href*="x.com"]',
        "instagram": 'a[href*="instagram.com"]',
        "linkedin": 'a[href*="linkedin.com"]',
        "youtube": 'a[href*="youtube.com"]',
        "tiktok": 'a[href*="tiktok.com"]',
        "pinterest": 'a[href*="pinterest.com"]',
    }
    found: list[str] = []
    for platform, selector in social.items():
        try:
            if response.css(selector):
                found.append(platform)
        except Exception:
            pass
    return found


def _is_parked(text: str) -> bool:
    signals = [
        "domain is for sale", "parked free", "buy this domain",
        "this domain is for sale", "powered by godaddy",
        "this page is under construction", "website coming soon",
        "default web page", "it works!", "welcome to nginx",
        "this domain has been registered", "coming soon",
    ]
    lower = text.lower()
    return any(s in lower for s in signals)


def _has_broken_layout(html_lower: str) -> bool:
    return any(s in html_lower for s in ["<frameset", "<marquee"])


def _detect_framework(html_lower: str) -> str:
    if any(s in html_lower for s in ["wp-content", "wp-includes", "/wp-json/"]):
        return "wordpress"
    if any(s in html_lower for s in ["wix-static", "wix-builder", "wix.com"]):
        return "wix"
    if "squarespace" in html_lower or "static1.squarespace" in html_lower:
        return "squarespace"
    if any(s in html_lower for s in ["shopify.com", "/cdn/shop/", "myshopify"]):
        return "shopify"
    if "webflow" in html_lower:
        return "webflow"
    if any(s in html_lower for s in ["drupal", "Drupal"]):
        return "drupal"
    if any(s in html_lower for s in ["joomla", "com_content"]):
        return "joomla"
    if any(s in html_lower for s in ["next/js", "__NEXT_DATA__", "next-static"]):
        return "nextjs"
    if "__NUXT__" in html_lower:
        return "nuxt"
    return "none"


def _empty_result(reason: str) -> dict:
    return {
        "overall_score": 0,
        "category": "hot",
        "issues": [reason],
        "emails_found": [],
        "phones_found": [],
        "raw_analysis": {
            "error": reason,
            "score_breakdown": {
                "deductions": [{"reason": reason, "points": -100, "severity": "critical"}],
                "bonuses": [],
                "deduction_total": -100,
                "bonus_total": 0,
                "summary": f"Analysis failed — {reason}",
            },
        },
    }
