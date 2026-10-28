import re
import sys
from pathlib import Path

if len(sys.argv) < 2:
    raise SystemExit("usage: update_readme.py <url>")

url = sys.argv[1].strip()
p = Path("README.md")
text = p.read_text(encoding="utf-8")

pattern = r"`(?:PENDING_URL|https://[a-z0-9-]+\.trycloudflare\.com)`"
new_text, n = re.subn(pattern, f"`{url}`", text)

if n == 0:
    # No placeholder found — inject a section
    new_text = text + f"\n\n## 🚀 Live URL\n\n> `{url}`\n"

p.write_text(new_text, encoding="utf-8")
print(f"[update_readme] replaced {n} placeholder(s) with {url}")
