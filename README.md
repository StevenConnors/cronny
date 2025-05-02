# Cronny

Cronny is a cron based on Github Actions and website parser that uses LLMs to detect and provide updates from specified websites.

## Quick Start

1. **Set your API key:**
   - Add your LLM API key as an environment variable (e.g., `OPENAI_API_KEY`).

2. **Configure websites to monitor:**
   - Edit `inputs.json` to add or change the list of websites and topics you want to track. Example:
     ```json
     [
       { "url": "https://example.com", "topic": "Example Topic" }
     ]
     ```

## Customization
- Update `inputs.json` to monitor any website and topic.
- Ensure your API key is set for LLM access. 