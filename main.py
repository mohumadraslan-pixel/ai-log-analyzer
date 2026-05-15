"""
AI-Powered Log Analyzer — Starter Template
Candidates should implement the TODO sections below.
"""

import os
import json
import uuid
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="AI Log Analyzer")

# ─── In-memory storage ────────────────────────────────────────────────
logs: list[dict] = []
alerts: list[dict] = []


# ─── Schemas ───────────────────────────────────────────────────────────
class LogEntry(BaseModel):
    source: str
    level: str  # INFO, WARN, ERROR, FATAL
    message: str
    timestamp: Optional[str] = None


class LogBatch(BaseModel):
    logs: list[LogEntry]


# ─── Endpoints ─────────────────────────────────────────────────────────

@app.post("/ingest")
def ingest_logs(batch: LogBatch):
    """
    Receive and store a batch of log entries.
    TODO: Normalize timestamps and handle malformed entries.
    """
    for entry in batch.logs:
        logs.append({
            "id": str(uuid.uuid4()),
            "source": entry.source,
            "level": entry.level,
            "message": entry.message,
            "timestamp": entry.timestamp or datetime.utcnow().isoformat(),
        })
    return {"ingested": len(batch.logs), "total": len(logs)}


@app.get("/logs")
def list_logs(level: Optional[str] = None, source: Optional[str] = None):
    """List stored logs with optional filters."""
    result = logs
    if level:
        result = [l for l in result if l["level"] == level.upper()]
    if source:
        result = [l for l in result if l["source"] == source]
    return result


# TODO: POST /analyze — Send recent logs to an LLM (e.g. Ollama) for anomaly detection
#   - Accept optional 'since' query param (ISO timestamp)
#   - Call OLLAMA_URL from env
#   - Parse the AI response for severity, root cause, and recommendation
#   - Generate an alert if anomaly score > threshold


# TODO: GET /alerts — List detected alerts with severity filtering


# TODO: GET /dashboard/stats — Return aggregate stats for the dashboard UI
#   - Total log count by level (INFO, WARN, ERROR, FATAL)
#   - Top 5 error sources
#   - Alert count by severity


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
