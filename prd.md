PRD — Daily Website Scraper (GitHub Actions)
Section	Detail
Doc Status	Draft v1 (2025‑05‑02)
Author	ChatGPT (for Steven C.)
Stakeholders	Steven C.
Target Ship Date	≤ 2025‑05‑10

1 · Problem
Steven manually checks a public webpage each day for new information.
He needs an automated, free solution to:

Fetch the page once per day.

Send the raw HTML to an LLM for parsing/extraction.

<sub>(Phase 2)</sub> Email him when relevant content appears.

2 · Goals & Non‑Goals
Goals (MVP)	Non‑Goals
Run once daily at a configurable time.	Sub‑daily or real‑time polling.
100 % free using GitHub Actions.	Owning/renting servers or containers.
Secure API keys in GitHub Secrets.	Building a full analytics dashboard.
Persist logs / upload JSON artifact.	Email alerts (deferred to Phase 2).

3 · User Stories
As Steven, I want the job to run daily so I never forget to look.

As Steven, failed runs appear red in GitHub Actions so I can debug quickly.

As Steven (Phase 2), I get an email only when pertinent info is found.

4 · Functional Spec
4.1 Trigger
on.schedule: default cron 0 15 * * * (00:00 JST / 15:00 UTC).

workflow_dispatch: manual “Run workflow” button.

4.2 Steps
Checkout repo.

Setup Python 3.11.

Install deps (requests, optional beautifulsoup4).

Run scripts/fetch_and_parse.py

Fetch URL with requests.

POST content to LLM (OPENAI_API_KEY).

Print JSON to stdout, upload as artifact.

Exit non‑zero on error → GitHub flags run red.

4.3 Secrets
Secret	Purpose
OPENAI_API_KEY	LLM call
Phase 2 SENDGRID_API_KEY or SMTP creds	Email sending

4.4 Outputs
GitHub Actions run log.

Optional artifact parsed.json (90‑day retention).

5 · Technical Design
markdown
Copy
Edit
.github/
  workflows/
    daily-scraper.yml
scripts/
  fetch_and_parse.py
requirements.txt
<details> <summary>**Workflow YAML (core)**</summary>
yaml
Copy
Edit
name: Daily Web Scraper

on:
  schedule:
    - cron: '0 15 * * *'
  workflow_dispatch:

jobs:
  scrape:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: python scripts/fetch_and_parse.py
</details> <details> <summary>**`fetch_and_parse.py` (outline)**</summary>
python
Copy
Edit
import os, requests, json, sys

URL = "https://example.com"
html = requests.get(URL, timeout=30).text

resp = requests.post(
    "https://api.openai.com/v1/chat/completions",
    headers={"Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}"},
    json={
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "Extract news about TOPIC."},
            {"role": "user", "content": html}
        ],
        "max_tokens": 300
    },
    timeout=30
)
parsed = resp.json()["choices"][0]["message"]["content"]

print(json.dumps({"parsed": parsed}))
</details>
6 · Phase 2 — Email Notification
Task	Detail
Dependency	pip install sendgrid (or SMTP lib)
Logic	If parsed matches regex/keyword → send email.
Secrets	SENDGRID_API_KEY, ALERT_EMAIL_TO

7 · Success Metrics
Metric	Target
Daily success rate	≥ 99 %
Runtime per run	≤ 60 s
Monthly Actions minutes	≤ 50 min (well under free 2 000)
False‑positive email alerts (Phase 2)	< 5 %

8 · Risks & Mitigations
Risk	Mitigation
Webpage layout changes break parsing.	Light pre‑LLM cleanup; unit tests; red run on exception.
LLM API outage or cost spike.	Cap max_tokens; monitor usage; fallback regex search.
Secrets accidentally printed.	Never echo secrets; use env vars only.

9 · Open Questions
Exact URL(s) & topics to monitor?

Preferred LLM provider/model?

Do we strip HTML before sending to LLM to save tokens?

Email provider choice for Phase 2 (SendGrid, SES, Gmail SMTP)?

10 · Timeline
Date	Milestone
May 03	Repo + Secrets created
May 05	MVP workflow green
May 07	Parsing & monitoring tweaks
May 10	Email POC (Phase 2)

