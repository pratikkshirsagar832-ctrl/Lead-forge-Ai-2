import os, sys
os.chdir("/root/leadforge/backend")
sys.path.insert(0, "/root/leadforge/backend")

# Manually load .env
with open("/root/leadforge/backend/.env") as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ[k.strip()] = v.strip()

from app.database import get_supabase_admin
s = get_supabase_admin()
leads = s.table("leads").select("id,lead_category,website_url").limit(5).execute()
print("leads count:", len(leads.data))
for l in leads.data:
    wa = s.table("website_analyses").select("overall_score,raw_analysis").eq("lead_id", l["id"]).execute()
    if wa.data:
        raw = wa.data[0].get("raw_analysis") or {}
        has_sb = "score_breakdown" in raw
        print(f"Lead {l['id'][:8]} cat={l['lead_category']} has_sb={has_sb} raw_keys={list(raw.keys())[:5]}")
    else:
        print(f"Lead {l['id'][:8]} NO analysis")
print("DONE")
