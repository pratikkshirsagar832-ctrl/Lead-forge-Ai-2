import json
import os

COOKIE_FILE = '/app/sessions/linkedin_session_8627ce24-6bd5-48b7-9b1f-595d042bfcf6.json'

SAMESITE_MAP = {
    'no_restriction': 'None',
    'unspecified': 'Lax',
    'none': 'None',
    'lax': 'Lax',
    'strict': 'Strict',
}

cookies = []

# Paste cookies
import sys
data = json.load(sys.stdin)
cookies = data if isinstance(data, list) else data.get('cookies', data)

normalized = []
for c in cookies:
    entry = dict(c)
    if 'expirationDate' in entry and 'expires' not in entry:
        entry['expires'] = int(entry.pop('expirationDate'))
    if 'expires' in entry and isinstance(entry['expires'], float):
        entry['expires'] = int(entry['expires'])
    ss = entry.get('sameSite', '')
    if ss and str(ss).lower() in SAMESITE_MAP:
        entry['sameSite'] = SAMESITE_MAP[str(ss).lower()]
    elif not ss or str(ss).lower() not in ('lax', 'strict', 'none'):
        entry['sameSite'] = 'Lax'
    normalized.append(entry)

with open(COOKIE_FILE, 'w') as f:
    json.dump({'cookies': normalized}, f)

print(f"Saved {len(normalized)} cookies")
print(f"Has li_at: {any(c.get('name') == 'li_at' for c in normalized)}")
