import json
import re
from datetime import date

import ollama

from .config import settings

_client = ollama.Client(host=settings.ollama_host)

EXTRACTION_PROMPT = """You are an assistant that extracts action items from meeting transcripts.

Today's date is {today}. Resolve relative dates ("Friday", "next week") against it.

Read the transcript and return a JSON array. Each element must have:
- "description": short imperative description of the task
- "owner": the person responsible, or null if not stated
- "deadline": an ISO date (YYYY-MM-DD) if a deadline is mentioned, else null
- "priority": one of "low", "medium", "high" (infer from urgency/language if not explicit)

Return ONLY the JSON array, no prose, no markdown fences. If there are no action
items, return [].

Transcript:
\"\"\"
{transcript}
\"\"\"
"""


def extract_json_array(text: str) -> list[dict]:
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if not match:
        return []
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return []


def extract_action_items(transcript: str) -> list[dict]:
    response = _client.chat(
        model=settings.ollama_model,
        messages=[
            {
                "role": "user",
                "content": EXTRACTION_PROMPT.format(today=date.today().isoformat(), transcript=transcript),
            }
        ],
        options={"temperature": 0},
    )
    return extract_json_array(response["message"]["content"])
