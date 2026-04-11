import os
import json
import sys

AUTH_STATE = os.path.join('.', 'merx_auth.json')

if not os.path.exists(AUTH_STATE):
    print(f"merx_auth.json not found at {AUTH_STATE}")
    sys.exit(1)

with open(AUTH_STATE, 'r', encoding='utf-8') as f:
    try:
        data = json.load(f)
    except Exception as e:
        print(f"Failed to parse {AUTH_STATE}: {e}")
        sys.exit(1)

cookies = data.get('cookies') or []
print(f"Total cookies in storage_state: {len(cookies)}")

# show domains and summary
domains = {}
for c in cookies:
    d = c.get('domain', '')
    domains.setdefault(d, 0)
    domains[d] += 1

if not domains:
    print("No cookie domains found.")
else:
    print("Cookie domains and counts:")
    for d, cnt in domains.items():
        print(f" - {d}: {cnt}")

# check for merx-related cookies
merx_cookies = [c for c in cookies if 'merx' in (c.get('domain') or '')]
if merx_cookies:
    print(f"Found {len(merx_cookies)} merx-related cookie(s):")
    for c in merx_cookies:
        name = c.get('name')
        domain = c.get('domain')
        path = c.get('path')
        http_only = c.get('httpOnly')
        secure = c.get('secure')
        val = c.get('value') or ''
        val_preview = (val[:6] + '...') if val else '<empty>'
        print(f"  - {name} @ {domain}{path} secure={secure} httpOnly={http_only} value={val_preview}")
else:
    print("No merx-related cookies found in merx_auth.json.")

# Quick sanity: check for idp cookie
idp = [c for c in cookies if 'idp.merx.com' in (c.get('domain') or '')]
if idp:
    print(f"Found {len(idp)} idp.merx.com cookie(s)")

print('\nIf merx cookies are present, try running merx_scraper.py next.')
