import os
import requests
import json
import sys
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env.local")

URL = "https://www.tetsudo.com/event/category/10009/"
TOPIC = "西武鉄道イベント"  # or any topic you want to extract

try:
    html = requests.get(URL, timeout=30).text
    # print(html)
except Exception as e:
    print(f"Error fetching URL: {e}", file=sys.stderr)
    sys.exit(1)

try:
    resp = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}", "Content-Type": "application/json"},
        json={
            "model": "gpt-4o",
            "messages": [
                {"role": "system", "content": f"Extract news about {TOPIC}. Keep the original language."},
                {"role": "user", "content": html}
            ],
            "max_tokens": 300
        },
        timeout=30
    )
    resp.raise_for_status()
    parsed = resp.json()["choices"][0]["message"]["content"]
except Exception as e:
    print(f"Error calling OpenAI API: {e}", file=sys.stderr)
    sys.exit(2)

print(json.dumps({"parsed": parsed}, ensure_ascii=False)) 