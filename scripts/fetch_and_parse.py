import os
import requests
import json
import sys
from dotenv import load_dotenv
import argparse
from bs4 import BeautifulSoup
from pathlib import Path

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

# Load previous results if available
previous_results = {}
if Path("latest_results.json").exists():
    try:
        with open("latest_results.json", "r", encoding="utf-8") as f:
            prev = json.load(f)
            for entry in prev:
                if 'url' in entry:
                    previous_results[entry['url']] = entry
    except Exception as e:
        print(f"Error reading previous results: {e}", file=sys.stderr)
        previous_results = {}

results = []
changes = []

for entry in input_data:
    URL = entry.get('url')
    TOPIC = entry.get('topic')
    if not URL or not TOPIC:
        print(f"Skipping entry with missing url or topic: {entry}", file=sys.stderr)
        continue
    try:
        html = requests.get(URL, timeout=30).text
        # Clean HTML: remove script, style, noscript tags
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        cleaned_text = soup.get_text(separator=" ", strip=True)
    except Exception as e:
        print(f"Error fetching or cleaning URL {URL}: {e}", file=sys.stderr)
        continue

    try:
        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}", "Content-Type": "application/json"},
            json={
                "model": "gpt-4.1-nano",
                "messages": [
                    {"role": "system", "content": f"Extract news about {TOPIC}. Keep the original language. Since the input text is HTML, make sure to remove any unnecessary tags or scripts so that the result is pure human readable text."},
                    {"role": "user", "content": cleaned_text}
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

    # Compare with previous result if available
    prev_parsed = previous_results.get(URL, {}).get("parsed", "")
    if prev_parsed:
        # Call LLM to compare
        try:
            diff_resp = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}", "Content-Type": "application/json"},
                json={
                    "model": "gpt-4.1-nano",
                    "messages": [
                        {"role": "system", "content": "You are a news change detector. Compare yesterday's and today's news summaries for the same topic and URL. If there are any new events, new text, or material changes, return a JSON object: {\"changed\": 1, \"title\": \"Short summary of what changed\"}. If nothing material changed, return {\"changed\": 0}."},
                        {"role": "user", "content": f"Yesterday's summary: {prev_parsed}\nToday's summary: {parsed}"}
                    ],
                    "max_tokens": 100
                },
                timeout=30
            )
            diff_resp.raise_for_status()
            diff_result = diff_resp.json()["choices"][0]["message"]["content"]
            print(diff_result)
            diff_json = json.loads(diff_result)
            if diff_json.get("changed") == 1:
                changes.append({
                    "url": URL,
                    "title": diff_json.get("title", "Text updated"),
                    "topic": TOPIC
                })
        except Exception as e:
            print(f"Error calling OpenAI diff API for URL {URL}: {e}", file=sys.stderr)
            continue
    else:
        # No previous result, treat as new
        changes.append({
            "url": URL,
            "title": "New entry or no previous data",
            "topic": TOPIC
        })

# Output changes.json if there are changes
if changes:
    with open("changes.json", "w", encoding="utf-8") as f:
        json.dump(changes, f, ensure_ascii=False, indent=2)
    # Save new results only if there are changes
    with open("latest_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    sys.exit(0)
else:
    print("No material changes detected.")
    sys.exit(1)