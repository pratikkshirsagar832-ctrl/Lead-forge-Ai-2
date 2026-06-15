"""
Hyperclients — Website Analyzer Service

Enhanced wrapper that combines multi-page crawling with Gemini deep analysis.
Delegates the heavy crawling to enhanced_analyzer, then passes the enriched
data to Gemini for AI-powered assessment.

Flow:
  1. enhanced_analyzer.analyze_website(url)  — multi-page crawl + signals
  2. gemini_analyzer.batch_deep_analyze([data])  — AI quality assessment
  3. Merge results and return
"""

import logging
from typing import Any

from app.services.enhanced_analyzer import analyze_website as enhanced_analyze
from app.services.gemini_analyzer import batch_deep_analyze

logger = logging.getLogger(__name__)


async def analyze_website(url: str) -> dict[str, Any]:
    result = await enhanced_analyze(url)

    if result.get("overall_score", 0) < 20:
        return result

    try:
        enriched = await batch_deep_analyze([result])
        if enriched and len(enriched) > 0:
            result = enriched[0]
            gemini = result.get("gemini_analysis", {})
            result["ai_notes"] = {
                "content_quality": gemini.get("content_quality_notes", ""),
                "technical_issues": gemini.get("technical_issues_found", []),
                "ux_issues": gemini.get("ux_issues_found", []),
                "trust_issues": gemini.get("trust_issues_found", []),
                "recommendation": gemini.get("recommendation_reason", ""),
            }
    except Exception as e:
        logger.warning(f"Gemini deep analysis failed for {url}: {e}")

    return result
