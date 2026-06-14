"""
Hyperclients — Gemini Deep Website Analyzer

Takes batch of Scrapling-extracted site data, sends to Gemini 2.5 Flash-Lite,
and returns deep analysis: content quality, SEO depth, UX issues, broken elements.

System prompt encodes knowledge from:
  - SEO-audit skill (technical SEO, content quality, international SEO)
  - AI-SEO skill (AI visibility, content extractability, agentic readiness)
  - Analytics skill (tracking, cookie consent, measurement)
  - Copywriting skill (content quality, CTA effectiveness, messaging)
  - Prospecting skill (lead qualification, website classification)

Performance: batches 5 sites per request. Only called for non-trivial sites (score >= 20).
"""

import json
import logging
import re
from typing import Any

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"
GEMINI_MODEL = "gemini-2.5-flash-lite"
BATCH_SIZE = 5

SYSTEM_PROMPT = """You are a senior website quality auditor and SEO specialist. Your job is to analyze website data extracted from live pages and provide deep, actionable assessments.

For each website provided, evaluate these dimensions and return a JSON assessment:

## Evaluation Dimensions

### 1. CONTENT QUALITY (0-30 points)
- Is the content valuable, well-written, and original? Or thin/generic?
- Does it serve clear search intent?
- Is there a clear value proposition above the fold?
- How is the writing quality (grammar, tone, clarity)?
- Is the content fresh or outdated?

### 2. TECHNICAL SEO (0-25 points)
- Are title tags and meta descriptions well-optimized?
- Is there proper heading hierarchy?
- Are internal links well-structured?
- Is the page loading efficiently based on size and structure?
- Are canonical URLs, hreflang, and language tags handled correctly?

### 3. USER EXPERIENCE & DESIGN (0-20 points)
- Is the design modern and professional?
- Is navigation clear and intuitive?
- Are CTAs visible and compelling?
- Is there a clear conversion path?
- Is the site mobile-friendly?

### 4. TRUST & AUTHORITY SIGNALS (0-15 points)
- Is there a privacy policy, terms, about page?
- Are there testimonials, case studies, or social proof?
- Is contact information visible?
- Are there security signals (SSL, trust badges)?

### 5. AI & SOCIAL READINESS (0-10 points)
- Is the content structured for AI extraction (FAQ schema, clear answers)?
- Are Open Graph and Twitter Card tags properly set?
- Is analytics (GA4/GTM) present?
- Is there a sitemap and robots.txt allowing crawlers?

## Output Format
Return a JSON array. For each website, include:
```json
{
  "url": "<website URL>",
  "content_quality_score": <0-30>,
  "technical_seo_score": <0-25>,
  "ux_score": <0-20>,
  "trust_score": <0-15>,
  "ai_readiness_score": <0-10>,
  "total_score": <0-100>,
  "content_quality_notes": "<brief note>",
  "technical_issues_found": ["<issue1>", "<issue2>"],
  "ux_issues_found": ["<issue1>"],
  "trust_issues_found": ["<issue1>"],
  "missing_features": ["<feature1>"],
  "recommended_category": "hot|warm|skip",
  "recommendation_reason": "<why this category>"
}
```

Scoring for recommended_category:
- hot (0-39): Serious issues, needs complete overhaul or has no real website
- warm (40-69): Has a site but significant room for improvement
- skip (70-100): Good website, low opportunity for web development services

Be strict but fair. A small local business site should be judged against reasonable expectations for its type, not against Fortune 500 standards."""  # noqa: E501


async def batch_deep_analyze(
    sites_data: list[dict],
) -> list[dict]:
    """
    Take a batch of Scrapling analysis results and run Gemini deep analysis.
    Returns enhanced results with AI-assessed scores and findings.
    """
    if not sites_data:
        return []

    settings = get_settings()
    if not settings.gemini_api_key:
        logger.warning("Gemini API key not set — skipping deep analysis")
        return sites_data

    all_enhanced: list[dict] = []

    for i in range(0, len(sites_data), BATCH_SIZE):
        batch = sites_data[i : i + BATCH_SIZE]
        try:
            enhanced = await _call_gemini_batch(batch)
            all_enhanced.extend(enhanced)
        except Exception as e:
            logger.error(f"Gemini batch analysis failed for batch {i // BATCH_SIZE}: {e}")
            # Fallback: return original data unchanged
            all_enhanced.extend(batch)

    return all_enhanced


async def _call_gemini_batch(batch: list[dict]) -> list[dict]:
    """Send a batch of site data to Gemini and parse the response."""
    settings = get_settings()

    # Build the batch prompt
    sites_json = []
    for site in batch:
        raw = site.get("raw_analysis", {})
        sites_json.append({
            "url": raw.get("final_url", site.get("url", "")),
            "title": raw.get("title", ""),
            "meta_description": raw.get("meta_description", ""),
            "framework": raw.get("framework", "unknown"),
            "language": raw.get("language", ""),
            "page_size_kb": raw.get("page_size_kb", 0),
            "visible_text_length": raw.get("visible_text_length", 0),
            "has_viewport": raw.get("has_viewport", False),
            "headings": raw.get("headings", {}),
            "internal_links": raw.get("internal_links", 0),
            "external_links": raw.get("external_links", 0),
            "total_images": raw.get("total_images", 0),
            "images_without_alt": raw.get("images_without_alt", 0),
            "social_platforms": raw.get("social_platforms", []),
            "has_structured_data": raw.get("has_structured_data", False),
            "schema_types": raw.get("schema_types", []),
            "has_analytics": raw.get("has_analytics", False),
            "has_cookie_consent": raw.get("has_cookie_consent", False),
            "form_count": raw.get("form_count", 0),
            "has_navigation": raw.get("has_navigation", False),
            "has_footer": raw.get("has_footer", False),
            "has_favicon": raw.get("has_favicon", False),
            "sitemap_found": raw.get("sitemap_found", False),
            "robots_ai_bots_blocked": raw.get("robots_ai_bots_blocked", []),
            "scrapling_score": site.get("overall_score", 50),
            "scrapling_issues": site.get("issues", []),
        })

    user_prompt = (
        "Analyze these websites for quality and opportunity assessment.\n"
        f"Return a JSON array with {len(sites_json)} entries, one per site in the same order.\n\n"
        f"WEBSITES DATA:\n{json.dumps(sites_json, indent=2)}"
    )

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{GEMINI_API_BASE}/models/{GEMINI_MODEL}:generateContent",
                params={"key": settings.gemini_api_key},
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [
                        {
                            "role": "user",
                            "parts": [{"text": user_prompt}],
                        }
                    ],
                    "systemInstruction": {
                        "parts": [{"text": SYSTEM_PROMPT}],
                    },
                    "generationConfig": {
                        "temperature": 0.3,
                        "maxOutputTokens": 4096,
                    },
                },
            )
            response.raise_for_status()
            data = response.json()

        text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        # Extract JSON array from response (handle markdown code blocks)
        json_str = _extract_json(text)
        gemini_results: list[dict] = json.loads(json_str)

        # Merge Gemini results back into original site data
        merged = []
        for site, gemini in zip(batch, gemini_results):
            enhanced = dict(site)
            enhanced["gemini_analysis"] = gemini
            enhanced["gemini_score"] = gemini.get("total_score", 50)

            # Blend Scrapling + Gemini scores (weighted: 40% scrapling, 60% gemini)
            scrapling_score = site.get("overall_score", 50)
            gemini_score = gemini.get("total_score", 50)
            blended = int(round(scrapling_score * 0.4 + gemini_score * 0.6))
            enhanced["overall_score"] = max(0, min(100, blended))

            # Use Gemini's category recommendation if available
            gemini_cat = gemini.get("recommended_category", "")
            if gemini_cat in ("hot", "warm", "skip"):
                enhanced["category"] = gemini_cat
            else:
                enhanced["category"] = _categorize(enhanced["overall_score"])

            # Merge issues: start with Scrapling issues, add Gemini issues
            all_issues = list(site.get("issues", []))
            for key in ("technical_issues_found", "ux_issues_found", "trust_issues_found", "missing_features"):
                for issue in gemini.get(key, []):
                    if issue and issue not in all_issues:
                        all_issues.append(issue)
            enhanced["issues"] = all_issues

            merged.append(enhanced)

        return merged

    except (json.JSONDecodeError, KeyError, IndexError, httpx.HTTPError) as e:
        logger.error(f"Gemini batch parse/request error: {e}")
        raise


def _extract_json(text: str) -> str:
    """Extract JSON array from text that may contain markdown code blocks.
    Handles nested brackets correctly (unlike naive regex).
    """
    m = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if m:
        text = m.group(1).strip()

    depth = 0
    start = -1
    for i, ch in enumerate(text):
        if ch == '[':
            if start == -1:
                start = i
            depth += 1
        elif ch == ']':
            depth -= 1
            if depth == 0 and start != -1:
                return text[start:i+1]
    return text


def _categorize(score: int) -> str:
    if score <= 39:
        return "hot"
    elif score <= 69:
        return "warm"
    return "skip"



