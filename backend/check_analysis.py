import os, sys
os.chdir("/root/leadforge/backend")
sys.path.insert(0, "/root/leadforge/backend")
with open(".env") as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ[k.strip()] = v.strip()
from app.database import get_supabase_admin
s = get_supabase_admin()

leads = s.table("leads").select("id,business_name,website_url,lead_category").eq("lead_category","hot").limit(5).execute()
for l in leads.data:
    wa = s.table("website_analyses").select("overall_score,raw_analysis").eq("lead_id", l["id"]).execute()
    if wa.data:
        a = wa.data[0]
        raw = a.get("raw_analysis") or {}
        sb = raw.get("score_breakdown", {})
        sep = "=" * 60
        print(sep)
        print(f"BIZ: {l['business_name'][:60]}")
        print(f"URL: {l['website_url']}")
        print(f"CAT: {l['lead_category']} SCORE: {a['overall_score']}")
        deductions = sb.get("deductions", [])
        bonuses = sb.get("bonuses", [])
        print(f"NUDE: {len(deductions)} deductions, {len(bonuses)} bonuses")
        for d in deductions[:8]:
            print(f"  [{d['severity']}] {d['reason']} ({d['points']})")
        for b in bonuses[:5]:
            print(f"  [+] {b['reason']} (+{b['points']})")
        print(f"SUM: {sb.get('summary','N/A')}")
    else:
        print(f"NO ANALYSIS for {l['business_name'][:40]}")
print("DONE")
