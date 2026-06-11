"""
LeadForge AI — Search Pipeline

Orchestrates the full search lifecycle:
  1. Initialize search row
  2. Run Google Maps scraper
  3. Parse + save leads
  4. Analyze websites (Phase 1: Scrapling, Phase 2: Gemini deep analysis)
  5. Finalize counts

Phase 1 runs Scrapling on all leads with websites (concurrent, semaphore 5).
Phase 2 batches non-trivial results (score >= 20) to Gemini for deep analysis.
"""

import asyncio
import logging
import time
from datetime import datetime, timezone

from app.database import get_supabase_admin
from app.services.analyzer_service import analyze_website
from app.services.gemini_analyzer import batch_deep_analyze
from app.services.scraper_service import run_maps_scraper

logger = logging.getLogger(__name__)

_search_semaphore = asyncio.Semaphore(3)
_active_searches: dict[str, bool] = {}

MAX_SEARCH_TIME_SECONDS = 600
MAX_RESULTS = 50
GEMINI_MIN_SCORE = 20  # Only batch sites with score >= this to Gemini


def is_search_cancelled(search_id: str) -> bool:
    return _active_searches.get(search_id, False)


def cancel_search(search_id: str) -> None:
    _active_searches[search_id] = True


async def run_search_pipeline(search_id: str, user_id: str, niche: str, location: str) -> None:
    supabase = get_supabase_admin()
    start_time = time.time()
    _active_searches[search_id] = False

    try:
        async with _search_semaphore:
            await _update_search(supabase, search_id, {
                "status": "scraping",
                "progress_percent": 5,
                "message": "Starting Google Maps search...",
            })

            if is_search_cancelled(search_id):
                await _mark_cancelled(supabase, search_id)
                return

            query = f"{niche} in {location}"
            elapsed = time.time() - start_time
            remaining_timeout = max(60, int(MAX_SEARCH_TIME_SECONDS - elapsed - 60))

            await _update_search(supabase, search_id, {
                "progress_percent": 10,
                "message": f"Scraping Google Maps for '{niche}' in {location}...",
            })

            try:
                raw_results = await run_maps_scraper(
                    query=query,
                    max_results=MAX_RESULTS,
                    timeout_seconds=remaining_timeout,
                )
            except Exception as e:
                logger.error(f"[Pipeline:{search_id}] Scraper failed: {e}")
                await _update_search(supabase, search_id, {
                    "status": "failed", "message": "Scraper failed",
                    "error_message": str(e), "progress_percent": 0,
                })
                return

            if is_search_cancelled(search_id):
                await _mark_cancelled(supabase, search_id)
                return

            if not raw_results:
                await _update_search(supabase, search_id, {
                    "status": "completed", "progress_percent": 100,
                    "message": "No results found. Try a different search.",
                    "total_results": 0,
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                })
                return

            await _update_search(supabase, search_id, {
                "progress_percent": 40,
                "message": f"Found {len(raw_results)} businesses. Saving leads...",
            })

            lead_ids = await _save_leads(supabase, search_id, user_id, raw_results)
            logger.info(f"[Pipeline:{search_id}] Saved {len(lead_ids)} leads")

            if is_search_cancelled(search_id):
                await _mark_cancelled(supabase, search_id)
                return

            # ── Stage 4: Analyze Websites ─────────────────────
            # Phase 1: Scrapling (all sites)
            # Phase 2: Gemini batch (non-trivial sites only)
            await _update_search(supabase, search_id, {
                "status": "analyzing",
                "progress_percent": 50,
                "message": "Analyzing websites...",
            })

            await _analyze_lead_websites_phase1(
                supabase, search_id, user_id, lead_ids, start_time
            )

            if is_search_cancelled(search_id):
                await _mark_cancelled(supabase, search_id)
                return

            await _analyze_lead_websites_phase2(
                supabase, search_id, start_time
            )

            if is_search_cancelled(search_id):
                await _mark_cancelled(supabase, search_id)
                return

            await _finalize_search(supabase, search_id)

    except Exception as e:
        logger.error(f"[Pipeline:{search_id}] Unexpected error: {e}", exc_info=True)
        try:
            await _update_search(supabase, search_id, {
                "status": "failed", "message": "Search failed unexpectedly",
                "error_message": str(e),
            })
        except Exception:
            pass
    finally:
        _active_searches.pop(search_id, None)
        _phase1_cache.pop(search_id, None)


async def _save_leads(
    supabase, search_id: str, user_id: str, raw_results: list[dict]
) -> list[str]:
    lead_ids = []
    for result in raw_results:
        try:
            has_website = bool(result.get("website_url"))
            lead_data = {
                "search_id": search_id,
                "user_id": user_id,
                "google_key": result.get("google_key", ""),
                "business_name": result.get("business_name", "Unknown"),
                "category": result.get("category", ""),
                "full_address": result.get("full_address", ""),
                "phone": result.get("phone", ""),
                "email_found": result.get("email_found", ""),
                "website_url": result.get("website_url", ""),
                "rating": result.get("rating"),
                "total_reviews": result.get("total_reviews", 0),
                "google_maps_link": result.get("google_maps_link", ""),
                "photos": result.get("photos", []),
                "business_hours": result.get("business_hours", {}),
                "description": result.get("description", ""),
                "lead_category": "warm" if has_website else "hot",
            }
            response = supabase.table("leads").insert(lead_data).execute()
            if response.data:
                lead_ids.append(response.data[0]["id"])
        except Exception as e:
            logger.error(f"Failed to save lead '{result.get('business_name', '?')}': {e}")
    return lead_ids


# ── PHASE 1: Scrapling Analysis ──────────────────────────────────────

async def _analyze_lead_websites_phase1(
    supabase, search_id: str, user_id: str, lead_ids: list[str], start_time: float,
) -> None:
    """Phase 1: Run Scrapling on all leads with websites (concurrent)."""
    try:
        response = (
            supabase.table("leads")
            .select("id, website_url, business_name")
            .eq("search_id", search_id)
            .neq("website_url", "")
            .execute()
        )
        leads_with_websites = response.data or []
    except Exception as e:
        logger.error(f"[Pipeline:{search_id}] Failed to fetch leads for Phase 1: {e}")
        return

    total = len(leads_with_websites)
    if total == 0:
        return

    analyzed = 0
    semaphore = asyncio.Semaphore(5)

    async def analyze_one(lead: dict) -> dict | None:
        nonlocal analyzed
        async with semaphore:
            elapsed = time.time() - start_time
            if elapsed > MAX_SEARCH_TIME_SECONDS:
                logger.warning(f"[Pipeline:{search_id}] Timeout in Phase 1")
                return None
            if is_search_cancelled(search_id):
                return None

            url = lead.get("website_url", "")
            lead_id = lead["id"]

            try:
                result = await analyze_website(url)

                # Save Phase 1 analysis to DB
                analysis_data = {
                    "lead_id": lead_id,
                    "website_url": url,
                    "overall_score": result.get("overall_score", 0),
                    "issues": result.get("issues", []),
                    "emails_found": result.get("emails_found", []),
                    "phones_found": result.get("phones_found", []),
                    "raw_analysis": result.get("raw_analysis", {}),
                }
                await asyncio.to_thread(
                    lambda: supabase.table("website_analyses").insert(analysis_data).execute()
                )

                update_data = {
                    "website_health_score": result.get("overall_score", 0),
                    "lead_category": result.get("category", "warm"),
                }
                emails = result.get("emails_found", [])
                if emails and not lead.get("email_found"):
                    update_data["email_found"] = emails[0]
                await asyncio.to_thread(
                    lambda: supabase.table("leads").update(update_data).eq("id", lead_id).execute()
                )

                analyzed += 1
                progress = 50 + int((analyzed / total) * 35)
                progress = min(progress, 85)
                try:
                    await _update_search(supabase, search_id, {
                        "progress_percent": progress,
                        "message": f"Scrapling: {analyzed}/{total} websites analyzed...",
                    })
                except Exception:
                    pass

                return {"lead_id": lead_id, "result": result}

            except Exception as e:
                logger.error(
                    f"[Pipeline:{search_id}] Phase 1 failed for {lead.get('business_name', '?')}: {e}"
                )
                analyzed += 1
                return None

    tasks = [analyze_one(lead) for lead in leads_with_websites]
    remaining = MAX_SEARCH_TIME_SECONDS - (time.time() - start_time)

    if remaining > 0:
        try:
            phase1_results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=max(30, remaining),
            )
        except asyncio.TimeoutError:
            logger.warning(f"[Pipeline:{search_id}] Phase 1 timed out — partial results")
            phase1_results = []
    else:
        phase1_results = []

    # Store results for Phase 2 (in a module-level dict as a simple cache)
    _phase1_cache[search_id] = [
        r for r in phase1_results
        if r and isinstance(r, dict) and r.get("result")
    ]


# Simple in-memory cache for Phase 1 results (per search)
_phase1_cache: dict[str, list[dict]] = {}


# ── PHASE 2: Gemini Deep Analysis ────────────────────────────────────

async def _analyze_lead_websites_phase2(
    supabase, search_id: str, start_time: float,
) -> None:
    """Phase 2: Batch non-trivial Phase 1 results to Gemini for deep analysis."""
    phase1_results = _phase1_cache.pop(search_id, [])
    if not phase1_results:
        return

    # Filter non-trivial sites (score >= GEMINI_MIN_SCORE)
    # Attach lead_id for result matching after batch processing
    gemini_candidates = []
    for entry in phase1_results:
        result = entry["result"]
        score = result.get("overall_score", 0)
        if score >= GEMINI_MIN_SCORE:
            result["_lead_id"] = entry["lead_id"]
            gemini_candidates.append(result)

    if not gemini_candidates:
        logger.info(f"[Pipeline:{search_id}] No sites qualify for Gemini deep analysis")
        # Mark Phase 2 progress as complete
        await _update_search(supabase, search_id, {
            "progress_percent": 90,
            "message": "All websites analyzed (Gemini skipped — all sites are trivial)",
        })
        return

    logger.info(
        f"[Pipeline:{search_id}] Sending {len(gemini_candidates)} sites to Gemini deep analysis"
    )

    elapsed = time.time() - start_time
    remaining = MAX_SEARCH_TIME_SECONDS - elapsed
    if remaining < 30:
        logger.warning(f"[Pipeline:{search_id}] Not enough time for Gemini — skipping")
        return

    try:
        await _update_search(supabase, search_id, {
            "progress_percent": 86,
            "message": f"Running AI deep analysis on {len(gemini_candidates)} websites...",
        })

        if is_search_cancelled(search_id):
            return

        enhanced_results = await asyncio.wait_for(
            batch_deep_analyze(gemini_candidates),
            timeout=min(remaining - 10, 120),
        )

        if is_search_cancelled(search_id):
            return

        # Update leads with Gemini-enhanced data
        updated = 0
        total = len(enhanced_results)
        for enhanced in enhanced_results:
            try:
                lead_id = enhanced.get("_lead_id", "")
                # Find the lead_id from phase1_results
                if not lead_id:
                    for entry in phase1_results:
                        if entry["result"].get("url") == enhanced.get("url"):
                            lead_id = entry["lead_id"]
                            break

                if not lead_id:
                    continue

                # Update lead with enhanced score + category
                supabase.table("leads").update({
                    "website_health_score": enhanced.get("overall_score", 0),
                    "lead_category": enhanced.get("category", "warm"),
                }).eq("id", lead_id).execute()

                # Update website_analyses row with enhanced score + issues
                supabase.table("website_analyses").update({
                    "overall_score": enhanced.get("overall_score", 0),
                    "issues": enhanced.get("issues", []),
                }).eq("lead_id", lead_id).execute()

                updated += 1
            except Exception as e:
                logger.error(
                    f"[Pipeline:{search_id}] Failed to save Gemini result for lead {lead_id}: {e}"
                )

            # Update progress
            progress = 86 + int((updated / total) * 9)
            progress = min(progress, 95)
            try:
                await _update_search(supabase, search_id, {
                    "progress_percent": progress,
                    "message": f"Deep AI analysis: {updated}/{total} enhanced...",
                })
            except Exception:
                pass

        logger.info(
            f"[Pipeline:{search_id}] Gemini enhanced {updated}/{total} sites"
        )

    except asyncio.TimeoutError:
        logger.warning(f"[Pipeline:{search_id}] Gemini Phase 2 timed out")
    except Exception as e:
        logger.error(f"[Pipeline:{search_id}] Gemini Phase 2 error: {e}")

    await _update_search(supabase, search_id, {
        "progress_percent": 95,
        "message": "Website analysis complete",
    })


# ── FINALIZE ─────────────────────────────────────────────────────────

async def _finalize_search(supabase, search_id: str) -> None:
    try:
        all_leads = (
            supabase.table("leads")
            .select("lead_category")
            .eq("search_id", search_id)
            .execute()
        )
        leads_data = all_leads.data or []

        total = len(leads_data)
        hot = sum(1 for l in leads_data if l.get("lead_category") == "hot")
        warm = sum(1 for l in leads_data if l.get("lead_category") == "warm")
        skip = sum(1 for l in leads_data if l.get("lead_category") == "skip")

        await _update_search(supabase, search_id, {
            "status": "completed",
            "progress_percent": 100,
            "message": f"Found {total} leads: {hot} hot, {warm} warm, {skip} skip",
            "total_results": total,
            "hot_leads": hot,
            "warm_leads": warm,
            "skipped": skip,
            "completed_at": datetime.now(timezone.utc).isoformat(),
        })

        logger.info(f"[Pipeline:{search_id}] Completed — {total} leads ({hot}H/{warm}W/{skip}S)")

    except Exception as e:
        logger.error(f"[Pipeline:{search_id}] Finalization failed: {e}")
        await _update_search(supabase, search_id, {
            "status": "completed",
            "progress_percent": 100,
            "message": "Search completed (finalization had issues)",
            "completed_at": datetime.now(timezone.utc).isoformat(),
        })


async def _mark_cancelled(supabase, search_id: str) -> None:
    await _update_search(supabase, search_id, {
        "status": "cancelled",
        "message": "Search cancelled by user",
        "completed_at": datetime.now(timezone.utc).isoformat(),
    })
    logger.info(f"[Pipeline:{search_id}] Cancelled")


async def _update_search(supabase, search_id: str, data: dict) -> None:
    try:
        supabase.table("searches").update(data).eq("id", search_id).execute()
    except Exception as e:
        logger.error(f"[Pipeline:{search_id}] Failed to update search: {e}")
