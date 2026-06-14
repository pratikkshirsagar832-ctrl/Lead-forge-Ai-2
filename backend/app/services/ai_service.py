"""
Hyperclients — AI Pitch Service

Generates professional outreach pitches using Gemini API.
On-demand only — not called automatically during search pipeline.
"""

import logging
from typing import Any, Optional

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"
GEMINI_MODEL = "gemini-2.0-flash-lite"


async def generate_pitch(
    lead: dict[str, Any],
    analysis: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    settings = get_settings()

    if not settings.gemini_api_key:
        return {
            "pitch": "AI pitch generation is not configured. Please set GEMINI_API_KEY.",
            "confidence_score": 0.0,
            "estimated_deal_value": 0.0,
        }

    prompt = _build_prompt(lead, analysis)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{GEMINI_API_BASE}/models/{GEMINI_MODEL}:generateContent",
                params={"key": settings.gemini_api_key},
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [
                        {
                            "role": "user",
                            "parts": [{"text": prompt}],
                        }
                    ],
                    "systemInstruction": {
                        "parts": [{
                            "text": (
                                "You are a professional sales copywriter helping freelance web developers "
                                "and digital marketing agencies write outreach messages. "
                                "Write concise, professional, and personalized outreach pitches. "
                                "Do NOT sound robotic or generic. Use the business details provided. "
                                "Keep it under 200 words. Include a clear value proposition and call to action."
                            )
                        }]
                    },
                    "generationConfig": {
                        "temperature": 0.7,
                        "maxOutputTokens": 500,
                    },
                },
            )
            response.raise_for_status()
            data = response.json()

        pitch_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        confidence = _calculate_confidence(lead, analysis)
        deal_value = _estimate_deal_value(lead, analysis)

        return {
            "pitch": pitch_text,
            "confidence_score": confidence,
            "estimated_deal_value": deal_value,
        }

    except httpx.TimeoutException:
        logger.error("Gemini API timeout")
        return {
            "pitch": "Pitch generation timed out. Please try again.",
            "confidence_score": 0.0,
            "estimated_deal_value": 0.0,
        }
    except Exception as e:
        logger.error(f"Pitch generation failed: {e}")
        return {
            "pitch": f"Pitch generation failed: {str(e)}",
            "confidence_score": 0.0,
            "estimated_deal_value": 0.0,
        }


def _build_prompt(lead: dict, analysis: Optional[dict] = None) -> str:
    parts = [
        f"Write a professional outreach pitch for this business:\n",
        f"Business Name: {lead.get('business_name', 'Unknown')}",
        f"Category: {lead.get('category', 'N/A')}",
    ]

    if lead.get("full_address"):
        parts.append(f"Location: {lead['full_address']}")

    if lead.get("website_url"):
        parts.append(f"Website: {lead['website_url']}")
    else:
        parts.append("Website: No website found")

    if lead.get("rating"):
        parts.append(f"Google Rating: {lead['rating']} ({lead.get('total_reviews', 0)} reviews)")

    if lead.get("phone"):
        parts.append(f"Phone: {lead['phone']}")

    if analysis:
        issues = analysis.get("issues", [])
        score = analysis.get("overall_score", None)
        if score is not None:
            parts.append(f"\nWebsite Health Score: {score}/100")
        if issues:
            parts.append("Website Issues Found:")
            for issue in issues[:5]:
                parts.append(f"  - {issue}")

    parts.append(
        "\nWrite a concise, professional pitch that:"
        "\n- Acknowledges their business specifically"
        "\n- Mentions specific website issues or opportunities if available"
        "\n- Offers a clear value proposition (web development, redesign, or digital marketing)"
        "\n- Has a friendly but professional call to action"
        "\n- Is suitable for email or LinkedIn outreach"
    )

    return "\n".join(parts)


def _calculate_confidence(lead: dict, analysis: Optional[dict] = None) -> float:
    score = 0.5
    if not lead.get("website_url"):
        score += 0.2
    if analysis:
        issue_count = len(analysis.get("issues", []))
        if issue_count > 3:
            score += 0.15
        elif issue_count > 1:
            score += 0.1
        web_score = analysis.get("overall_score", 50)
        if web_score < 30:
            score += 0.15
        elif web_score < 50:
            score += 0.1
    reviews = lead.get("total_reviews", 0)
    rating = lead.get("rating", 0)
    if reviews > 10 and rating and rating < 4.0:
        score += 0.05
    if lead.get("phone"):
        score += 0.05
    return min(1.0, round(score, 2))


def _estimate_deal_value(lead: dict, analysis: Optional[dict] = None) -> float:
    base_value = 500.0
    if not lead.get("website_url"):
        base_value = 2000.0
    elif analysis:
        issue_count = len(analysis.get("issues", []))
        if issue_count > 4:
            base_value = 1500.0
        elif issue_count > 2:
            base_value = 1000.0
    reviews = lead.get("total_reviews", 0)
    if reviews > 100:
        base_value *= 1.5
    elif reviews > 50:
        base_value *= 1.3
    elif reviews > 20:
        base_value *= 1.1
    return round(base_value, 2)


async def generate_website_message(
    lead: dict[str, Any],
    analysis: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    settings = get_settings()

    if not settings.gemini_api_key:
        return {
            "message": (
                f"Hi {lead.get('business_name', 'there')}! "
                f"I noticed your website could use some improvements. "
                f"Would you be open to a quick chat about how I can help?"
            ),
        }

    prompt = _build_website_message_prompt(lead, analysis)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{GEMINI_API_BASE}/models/{GEMINI_MODEL}:generateContent",
                params={"key": settings.gemini_api_key},
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [
                        {
                            "role": "user",
                            "parts": [{"text": prompt}],
                        }
                    ],
                    "systemInstruction": {
                        "parts": [{
                            "text": (
                                "You are a professional web consultant reaching out to business owners. "
                                "Write a short, personalized WhatsApp message that mentions specific issues "
                                "found on their website. Keep it under 120 words. Friendly but professional. "
                                "Include a clear call to action. Do NOT use markdown. Do NOT use emojis. "
                                "Write in plain text suitable for WhatsApp."
                            )
                        }]
                    },
                    "generationConfig": {
                        "temperature": 0.7,
                        "maxOutputTokens": 300,
                    },
                },
            )
            response.raise_for_status()
            data = response.json()

        message_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        return {"message": message_text}

    except httpx.TimeoutException:
        logger.error("Gemini API timeout for website message")
        return {
            "message": (
                f"Hi {lead.get('business_name', 'there')}! "
                f"I recently reviewed your website and noticed a few areas "
                f"that could be improved. Would you be open to a quick chat?"
            ),
        }
    except Exception as e:
        logger.error(f"Website message generation failed: {e}")
        return {
            "message": (
                f"Hi {lead.get('business_name', 'there')}! "
                f"I can help improve your online presence. "
                f"Would you be open to a quick conversation?"
            ),
        }


def _build_website_message_prompt(lead: dict, analysis: Optional[dict] = None) -> str:
    parts = [
        f"Write a short WhatsApp outreach message for this business:\n",
        f"Business Name: {lead.get('business_name', 'Unknown')}",
        f"Category: {lead.get('category', 'N/A')}",
    ]

    if lead.get("full_address"):
        parts.append(f"Location: {lead['full_address']}")

    if lead.get("website_url"):
        parts.append(f"Website: {lead['website_url']}")
    else:
        parts.append("Website: No website found — they need one built")

    if lead.get("phone"):
        parts.append(f"Phone: {lead['phone']}")

    if analysis:
        score = analysis.get("overall_score", 0)
        parts.append(f"Website Health Score: {score}/100")
        issues = analysis.get("issues", [])
        if issues:
            parts.append("Website Issues Found:")
            for issue in issues[:4]:
                parts.append(f"  - {issue}")
        raw = analysis.get("raw_analysis", {})
        breakdown = raw.get("score_breakdown", {})
        if breakdown:
            deductions = breakdown.get("deductions", [])
            criticals = [d for d in deductions if d.get("severity") == "critical"]
            if criticals:
                parts.append("Critical Issues:")
                for c in criticals[:3]:
                    parts.append(f"  - {c.get('reason', '')}")

    parts.append(
        "\nWrite a short WhatsApp message that:"
        "\n- Greets them by business name"
        "\n- Mentions 1-2 specific issues found on their website"
        "\n- Offers your help in a friendly, non-pushy way"
        "\n- Has a clear call to action (reply or call)"
        "\n- Is under 120 words, plain text, no markdown, no emojis"
    )

    return "\n".join(parts)
