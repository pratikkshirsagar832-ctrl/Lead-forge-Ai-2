import json, sys
d = json.load(sys.stdin)
data = d.get("data", d.get("leads", []))
print("Total leads:", len(data))
for l in data[:3]:
    wa = l.get("website_analyses", [])
    print(f"{l['id'][:8]} cat={l['lead_category']} wa_count={len(wa)}")
    for a in wa:
        raw = a.get("raw_analysis") or {}
        print(f"  score={a['overall_score']} has_sb={'score_breakdown' in raw}")
