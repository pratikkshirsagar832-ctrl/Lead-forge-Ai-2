"""
LeadForge AI — Website Analyzer Service (Phase 1 Enhanced)

Uses Scrapling's AsyncFetcher + Selector for 28+ quality signals.
Categorizes leads:
  - hot  (score 0-39)   — bad/no website = great opportunity
  - warm (score 40-69)  — mediocre website = some opportunity
  - skip (score 70-100) — good website = low opportunity

Phase 1 enhancements (from SEO-audit + AI-SEO skills):
  - Heading hierarchy (h1-h6), internal vs external links, language tag
  - Canonical tag, robots.txt AI-bot detection, GA4/GTM snippets
  - Schema type identification, Twitter Cards, cookie consent
  - Image lazy loading, link anchor text ratio, form detection
"""

import asyncio
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

    issues: list[str] = []
    raw: dict[str, Any] = {}
    emails_found: list[str] = []
    phones_found: list[str] = []
    score = 100
    parsed_url = urlparse(url)
    base_domain = parsed_url.netloc

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

        # Update base_domain after redirects
        if hasattr(response, "url"):
            parsed_url = urlparse(str(response.url))
            base_domain = parsed_url.netloc
            url = str(response.url)

        # ── SSL/HTTPS ────────────────────────────────────────────
        is_https = str(response.url).startswith("https://")
        raw["is_https"] = is_https
        if not is_https:
            issues.append("No HTTPS")
            score -= 15

        # ── Title ────────────────────────────────────────────────
        title_el = response.css("title::text")
        title = title_el.get() if title_el else ""
        raw["title"] = str(title) if title else ""
        if not title:
            issues.append("Missing page title")
            score -= 10
        elif len(str(title).strip()) < 10:
            issues.append("Title too short")
            score -= 5

        # ── Meta description ─────────────────────────────────────
        meta_el = response.find("meta", {"name": "description"})
        desc = meta_el.attrib.get("content", "") if meta_el else ""
        raw["meta_description"] = str(desc) if desc else ""
        if not desc:
            issues.append("Missing meta description")
            score -= 10
        elif len(str(desc).strip()) < 50:
            issues.append("Meta description too short")
            score -= 5

        # ── LANGUAGE TAG (new - SEO audit skill) ─────────────────
        html_el = response.find("html")
        lang = html_el.attrib.get("lang", "") if html_el else ""
        raw["language"] = lang or ""
        if not lang:
            issues.append("Missing HTML lang attribute")
            score -= 3

        # ── CANONICAL TAG (new - SEO audit skill) ────────────────
        canonical_el = response.find("link", {"rel": "canonical"})
        canonical_href = canonical_el.attrib.get("href", "") if canonical_el else ""
        raw["canonical_url"] = canonical_href or ""
        if not canonical_href:
            issues.append("No canonical tag")
            score -= 3

        # ── CONTENT LENGTH ───────────────────────────────────────
        visible_text = str(response.get_all_text(separator=" ", strip=True) or "")
        text_len = len(visible_text)
        raw["visible_text_length"] = text_len
        if text_len < 200:
            issues.append("Very thin content")
            score -= 15
        elif text_len < 500:
            issues.append("Thin content")
            score -= 8

        # ── CONTACT INFO ─────────────────────────────────────────
        full_text = str(response.get_all_text(separator="\n", strip=True) or "")
        emails_found = _extract_emails(full_text)
        phones_found = _extract_phones(full_text)
        raw["emails_count"] = len(emails_found)
        raw["phones_count"] = len(phones_found)
        if not emails_found and not phones_found:
            issues.append("No contact info found")
            score -= 10

        # ── SOCIAL PRESENCE ──────────────────────────────────────
        social = _extract_social_links(response)
        raw["social_platforms"] = social
        raw["social_count"] = len(social)
        if not social:
            issues.append("No social media presence")
            score -= 5
        elif len(social) >= 3:
            score += 5

        # ── PARKED / TEMPLATE ────────────────────────────────────
        if _is_parked(visible_text):
            issues.append("Site appears parked or default template")
            score -= 25

        # ── BROKEN LAYOUT ────────────────────────────────────────
        html_content = str(
            getattr(response, 'html_content', None)
            or getattr(response, 'text', None)
            or (response.body or b"").decode('utf-8', errors='replace')
        )
        html_lower = html_content.lower()
        if _has_broken_layout(html_lower):
            issues.append("Outdated or broken layout")
            score -= 10

        # ── MOBILE VIEWPORT ──────────────────────────────────────
        has_viewport = bool(response.find("meta", {"name": "viewport"}))
        raw["has_viewport"] = has_viewport
        if not has_viewport:
            issues.append("Not mobile-friendly (no viewport meta)")
            score -= 10

        # ── FRAMEWORK DETECTION ──────────────────────────────────
        framework = _detect_framework(html_lower)
        raw["framework"] = framework
        if framework == "none":
            issues.append("No modern CMS/framework detected")
            score -= 5
        elif framework in ("wix", "squarespace", "shopify", "webflow"):
            score += 5
        elif framework == "wordpress":
            score += 3

        # ── OPEN GRAPH TAGS ──────────────────────────────────────
        og_tags = response.css('meta[property^="og:"]')
        og_count = len(og_tags)
        raw["og_tags_count"] = og_count
        if og_count < 3:
            issues.append("Poor social sharing (missing Open Graph tags)")
            score -= 5

        # ── TWITTER CARDS (new - SEO audit skill) ────────────────
        twitter_tags = response.css('meta[name^="twitter:"]')
        raw["twitter_card_count"] = len(twitter_tags)
        if not twitter_tags:
            issues.append("No Twitter Card meta tags")
            score -= 3

        # ── FAVICON ──────────────────────────────────────────────
        has_favicon = bool(
            response.css('link[rel="icon"]')
            or response.css('link[rel="shortcut icon"]')
            or response.css('link[rel="apple-touch-icon"]')
        )
        raw["has_favicon"] = has_favicon
        if not has_favicon:
            issues.append("No favicon")
            score -= 3

        # ── HEADING HIERARCHY (new - SEO audit skill) ───────────
        headings = {}
        for tag in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            els = response.css(tag)
            headings[tag] = len(els)
        raw["headings"] = headings
        if headings["h1"] == 0:
            issues.append("No H1 heading")
            score -= 5
        elif headings["h1"] > 1:
            issues.append(f"Multiple H1 tags ({headings['h1']})")
            score -= 3
        if headings["h2"] == 0 and text_len > 500:
            issues.append("No H2 subheadings despite substantial content")
            score -= 3

        # ── INTERNAL vs EXTERNAL LINKS (new - SEO audit skill) ──
        all_links = response.css("a[href]")
        internal = 0
        external = 0
        nofollow = 0
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
        total_links = internal + external
        raw["internal_links"] = internal
        raw["external_links"] = external
        raw["nofollow_links"] = nofollow
        raw["total_links"] = total_links
        if total_links == 0:
            issues.append("No internal links found")
            score -= 5
        elif external > 0 and external / total_links > 0.5:
            issues.append("Most links point to external sites")
            score -= 3

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
            issues.append("Many images missing alt text")
            score -= 5
        if total_imgs > 0 and webp / total_imgs < 0.3:
            issues.append("Most images not in WebP/AVIF format")
            score -= 3

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
            issues.append("No structured data (schema.org)")
            score -= 5
        elif "LocalBusiness" not in schema_types and "Organization" not in schema_types:
            issues.append("Missing LocalBusiness/Organization schema")
            score -= 2

        # ── GA4 / GTM DETECTION (new - analytics skill) ─────────
        has_ga = bool(
            re.search(r'gtag\s*\(|google-analytics\.com|googletagmanager\.com', html_lower)
        )
        raw["has_analytics"] = has_ga
        if not has_ga:
            issues.append("No analytics detected (GA4/GTM)")
            score -= 3

        # ── COOKIE CONSENT (new - analytics skill) ──────────────
        has_cookie_banner = bool(
            re.search(
                r'cookie[-_]?(consent|banner|notice|popup|bar)',
                html_lower,
            )
            or response.css('[class*="cookie"], [id*="cookie"], [class*="CookieConsent"]')
        )
        raw["has_cookie_consent"] = has_cookie_banner
        if not has_cookie_banner:
            issues.append("No cookie consent banner detected")
            score -= 2

        # ── FORM DETECTION (new - prospecting skill) ────────────
        forms = response.css("form")
        raw["form_count"] = len(forms)
        if forms:
            cta_inputs = response.css('button[type="submit"], input[type="submit"]')
            raw["cta_button_count"] = len(cta_inputs)
        else:
            raw["cta_button_count"] = 0

        # ── NAVIGATION ───────────────────────────────────────────
        has_nav = bool(
            response.css("nav, header nav, .nav, .navbar, #nav, #navbar")
        )
        raw["has_navigation"] = has_nav
        if not has_nav:
            issues.append("No visible navigation")
            score -= 5

        # ── FOOTER ───────────────────────────────────────────────
        has_footer = bool(response.css("footer, .footer, #footer"))
        raw["has_footer"] = has_footer
        if not has_footer:
            issues.append("No footer found")
            score -= 3

        # ── PAGE SIZE ────────────────────────────────────────────
        if raw["page_size_kb"] > 3000:
            issues.append(f"Very large page ({raw['page_size_kb']:.0f} KB)")
            score -= 5
        elif raw["page_size_kb"] < 5:
            issues.append("Suspiciously small page")
            score -= 5

        # ── ROBOTS.TXT CHECK (new - AI-SEO skill) ──────────────
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
                    issues.append(f"AI crawlers blocked in robots.txt ({', '.join(ai_bots_blocked)})")
                    score -= 2
            else:
                raw["robots_txt_found"] = False
        except Exception:
            raw["robots_txt_found"] = False

        # ── SITEMAP DETECTION (new - SEO audit skill) ───────────
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
            issues.append("No XML sitemap detected")
            score -= 3

        # ── CLAMP & CATEGORIZE ──────────────────────────────────
        score = max(0, min(100, score + _bonus_from_signals(raw)))
        raw["final_score"] = score

        if score <= HOT_MAX:
            category = "hot"
        elif score <= WARM_MAX:
            category = "warm"
        else:
            category = "skip"

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


def _bonus_from_signals(raw: dict) -> int:
    bonus = 0
    if raw.get("has_navigation"): bonus += 2
    if raw.get("has_footer"): bonus += 1
    if raw.get("has_viewport"): bonus += 2
    if raw.get("has_favicon"): bonus += 1
    if raw.get("has_structured_data"): bonus += 2
    if raw.get("has_analytics"): bonus += 1
    if raw.get("sitemap_found"): bonus += 1
    if raw.get("has_cookie_consent"): bonus += 1
    if raw.get("canonical_url"): bonus += 1
    if raw.get("language"): bonus += 1
    h = raw.get("headings", {})
    if h.get("h1") == 1: bonus += 2
    if h.get("h2", 0) >= 3: bonus += 1
    return bonus


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
        "raw_analysis": {"error": reason},
    }
