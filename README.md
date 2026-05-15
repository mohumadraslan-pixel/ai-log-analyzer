# AI-Powered Log Analyzer Starter

A starter template for building a log analysis microservice with FastAPI and LLM integration.

## Getting Started

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

## What to Implement

| Endpoint | File | Description |
|----------|------|-------------|
| POST /ingest | `main.py` | Already implemented — log ingestion |
| GET /logs | `main.py` | Already implemented — list/filter logs |
| POST /analyze | `main.py` | Send logs to Ollama/OpenAI for anomaly detection |
| GET /alerts | `main.py` | List detected security alerts |
| GET /dashboard/stats | `main.py` | Aggregate stats for the dashboard UI |

## Notes

- Server runs on port 8000 by default (override with `PORT` env)
- Logs are stored in memory (swap with ClickHouse or PostgreSQL later)
- LLM endpoint defaults to `http://localhost:11434` (Ollama)
