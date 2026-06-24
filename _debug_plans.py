"""Debug script to test plans API from inside the Docker container"""
import httpx
import urllib.request
import json

URL = "https://wtradahkkpbkbhmkkpal.supabase.co/rest/v1/plans?select=*"
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind0cmFkYWhra3Bia2JobWtrcGFsIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4MTAwNzI2NywiZXhwIjoyMDk2NTgzMjY3fQ.QUKn8jhwCSyT1mnsMIq4dhPZND7xzG5VWxO5heO4fJI"
HEADERS = {
    "apikey": API_KEY,
    "Authorization": f"Bearer {API_KEY}",
}

print("=== Test 1: urllib (standard library) ===")
try:
    req = urllib.request.Request(URL, headers=HEADERS)
    with urllib.request.urlopen(req) as resp:
        print(f"status: {resp.status}")
        print(f"headers: {dict(resp.headers)}")
        body = resp.read().decode()
        print(f"body: {body[:200]}")
        print(f"len: {len(body)}")
except Exception as e:
    print(f"error: {e}")

print("\n=== Test 2: httpx (default User-Agent) ===")
try:
    r = httpx.get(URL, headers=HEADERS)
    print(f"status: {r.status_code}")
    print(f"req_headers: {dict(r.request.headers)}")
    print(f"resp_headers: {dict(r.headers)}")
    print(f"body: {r.text[:200]}")
    print(f"len: {len(r.text)}")
except Exception as e:
    print(f"error: {e}")

print("\n=== Test 3: httpx (Mozilla User-Agent) ===")
try:
    ua_headers = {**HEADERS, "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    r = httpx.get(URL, headers=ua_headers)
    print(f"status: {r.status_code}")
    print(f"body: {r.text[:200]}")
    print(f"len: {len(r.text)}")
except Exception as e:
    print(f"error: {e}")

print("\n=== Test 4: httpx (no apikey header, only Authorization) ===")
try:
    r = httpx.get(URL, headers={"Authorization": f"Bearer {API_KEY}"})
    print(f"status: {r.status_code}")
    print(f"body: {r.text[:200]}")
    print(f"len: {len(r.text)}")
except Exception as e:
    print(f"error: {e}")
