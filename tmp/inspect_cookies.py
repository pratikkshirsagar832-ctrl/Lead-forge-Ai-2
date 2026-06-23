import json
with open('/app/sessions/linkedin_session_8627ce24-6bd5-48b7-9b1f-595d042bfcf6.json') as f:
    data = json.load(f)
cookies = data.get('cookies', [])
print(f'Total cookies: {len(cookies)}')
for c in cookies:
    name = c.get('name', '')
    domain = c.get('domain', '')
    val_preview = c.get('value', '')[:25]
    print(f'  {name:25s} domain={domain:25s} value={val_preview}...')
li_at = [c for c in cookies if c.get('name') == 'li_at']
if li_at:
    print(f'\nli_at keys: {list(li_at[0].keys())}')
    print(f'li_at domain: {li_at[0].get("domain")}')
    print(f'li_at value preview: {li_at[0].get("value", "")[:30]}')
else:
    print('\nNO li_at in cookies!')
