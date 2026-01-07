import requests
import re
import html
import json

session = requests.Session()

# Get login page
resp = session.get("http://localhost:8088/login/")
print("Login page sample:", resp.text[:1000])

# Try different CSRF patterns
patterns = [
    r'name="csrf_token".*?value="([^"]+)"',
    r'value="([^"]+)".*?name="csrf_token"',
    r'id="csrf_token".*?value="([^"]+)"',
    r'"csrf_token"\s*:\s*"([^"]+)"',
    r'WTF_CSRF_SECRET_KEY.*?"([^"]+)"',
]

csrf = ""
for pattern in patterns:
    match = re.search(pattern, resp.text, re.DOTALL)
    if match:
        csrf = match.group(1)
        print(f"Found CSRF with pattern: {pattern[:30]}...")
        break

print("CSRF token:", csrf[:50] + "..." if csrf else "NOT FOUND")
