import os, sys
os.chdir("/root/leadforge")
sys.path.insert(0, "/root/leadforge")
os.environ["SUPABASE_URL"] = "https://dxrxlpcjejzqjtgrdgbm.supabase.co"
os.environ["SUPABASE_KEY"] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImR4cnhscGNqZWp6cWp0Z3JkZ2JtIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0MzgzNTcxMCwiZXhwIjoyMDU5NDExNzEwfQ.ePMxhQ8xWrwjySzFTZ3AlgV76TAmQGFB2B0MpWhFsTI"
from app.database import get_supabase_admin
s = get_supabase_admin()
for t in ["email_logs","phone_numbers_extracted","website_analyses","leads"]:
    r = s.table(t).delete().neq("id","00000000-0000-0000-0000-000000000000").execute()
    print(f"{t}: {len(r.data)} deleted")
r = s.table("searches").update({"status":"completed","total_leads":0}).neq("id","00000000-0000-0000-0000-000000000000").execute()
print(f"searches reset: {len(r.data)}")
print("Done")
