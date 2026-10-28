import re
import sys
from pathlib import Path

if len(sys.argv) < 2:
    raise SystemExit("usage: update_readme.py <url>")

url = sys.argv[1].strip()
p = Path("README.md")

# Check if README.md exists
if not p.exists():
    # Create a default README if it doesn't exist
    default_content = f"""# 🌈 IRIS

> Created by **MUHAMMAD TAQI**

**Check all software and like for best software!**  
The most-liked software automatically rises to the **top** of the list.

## 🚀 Live URL (TryCloudflare)

> **Current live URL:** `{url}`
"""
    p.write_text(default_content, encoding="utf-8")
    print(f"[update_readme] README.md not found. Created new file with URL: {url}")
else:
    # If file exists, update the URL
    text = p.read_text(encoding="utf-8")
    pattern = r"`(?:PENDING_URL|https://[a-z0-9-]+\.trycloudflare\.com)`"
    new_text, n = re.subn(pattern, f"`{url}`", text)

    if n == 0:
        # If no placeholder found, append a section
        new_text = text + f"\n\n## 🚀 Live URL\n\n> `{url}`\n"

    p.write_text(new_text, encoding="utf-8")
    print(f"[update_readme] Replaced {n} placeholder(s) with {url}")
