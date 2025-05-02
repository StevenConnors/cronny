import os
import requests
import json
import sys
from dotenv import load_dotenv
import argparse

load_dotenv(dotenv_path=".env.local")

def parse_args():
    parser = argparse.ArgumentParser(description="Fetch and parse news topics from URLs.")
    parser.add_argument('--input', type=str, default='inputs.json', help='Path to input JSON file with URLs and topics')
    return parser.parse_args()

args = parse_args()

# Read input file
try:
    with open(args.input, 'r', encoding='utf-8') as f:
        input_data = json.load(f)
except Exception as e:
    print(f"Error reading input file {args.input}: {e}", file=sys.stderr)
    sys.exit(4)

results = []

for entry in input_data:
    URL = entry.get('url')
    TOPIC = entry.get('topic')
    if not URL or not TOPIC:
        print(f"Skipping entry with missing url or topic: {entry}", file=sys.stderr)
        continue
    try:
        html = requests.get(URL, timeout=30).text
    except Exception as e:
        print(f"Error fetching URL {URL}: {e}", file=sys.stderr)
        continue

    try:
        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}", "Content-Type": "application/json"},
            json={
                "model": "gpt-4.1-nano",
                "messages": [
                    {"role": "system", "content": f"Extract news about {TOPIC}. Keep the original language. Since the input text is HTML, make sure to remove any unnecessary tags or scripts so that the result is pure human readable text."},
                    {"role": "user", "content": html}
                ],
                "max_tokens": 300
            },
            timeout=30
        )
        resp.raise_for_status()
        parsed = resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"Error calling OpenAI API for URL {URL}: {e}", file=sys.stderr)
        continue

    results.append({"url": URL, "topic": TOPIC, "parsed": parsed})

# Save to latest_results.json
with open("latest_results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(json.dumps(results, ensure_ascii=False))