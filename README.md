# ActionLoop

AI assistant that turns meeting transcripts into tracked action items, with a human-in-the-loop
review step and a weekly initiative status report.

## Stack

- FastAPI — HTTP API
- LangGraph — extract → normalize pipeline over the transcript
- Ollama (local LLM) — action item extraction
- faster-whisper — local audio transcription
- PostgreSQL + SQLAlchemy — storage
- APScheduler — weekly report cron job

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # edit DATABASE_URL if needed; OLLAMA_MODEL defaults to llama3
uvicorn app.main:app --reload
```

Postgres must be running and reachable at `DATABASE_URL`; tables are created automatically on
startup.

## Flow

1. `POST /meetings` (raw transcript) or `POST /meetings/upload-audio` (audio file, transcribed
   locally via faster-whisper) — runs the LangGraph extraction pipeline and stores action items
   with `status=pending_review`.
2. `GET /action-items?status=pending_review` — see what the AI extracted.
3. `PATCH /action-items/{id}` — human approves, edits, rejects, or assigns an item to an
   initiative. This is the human-in-the-loop gate.
4. `GET /initiatives` — dashboard: per-initiative totals, completed count, overdue count.
5. `POST /reports/weekly/generate` — builds a markdown report (also runs automatically every
   Monday 8am via APScheduler). `GET /reports/weekly/preview` returns it without saving.

## Tests

No framework needed — each test file is self-checking:

```bash
python -m tests.test_graph
python -m tests.test_reports
```
