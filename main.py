
"""
AI-Powered Log Analyzer — Completed Solution
"""

import os
import json
import uuid
from collections import Counter
from datetime import datetime
from typing import Optional

import requests
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


# ─── Helpers ───────────────────────────────────────────────────────────
VALID_LEVELS = {"INFO", "WARN", "ERROR", "FATAL"}


def normalize_timestamp(ts: Optional[str]) -> str:
    """
    Convert timestamp to ISO format.
    If invalid or missing, return current UTC timestamp.
    """
    if not ts:
        return datetime.utcnow().isoformat()

    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).isoformat()
    except Exception:
        return datetime.utcnow().isoformat()


def call_ollama(log_subset: list[dict]) -> dict:
    """
    Send logs to Ollama for anomaly detection.
    Expected JSON response:
    {
      "severity": "HIGH",
      "root_cause": "...",
      "recommendation": "...",
      "anomaly_score": 0.92
    }
    """

    ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
    model = os.getenv("OLLAMA_MODEL", "llama3")

    prompt = f"""
Analyze the following application logs.

Logs:
{json.dumps(log_subset, indent=2)}

Return ONLY valid JSON:

{{
  "severity": "LOW|MEDIUM|HIGH|CRITICAL",
  "root_cause": "short explanation",
  "recommendation": "recommended action",
  "anomaly_score": 0.0
}}
"""

    try:
        response = requests.post(
            ollama_url,
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
            },
            timeout=30,
        )

        response.raise_for_status()

        data = response.json()

        raw_text = data.get("response", "").strip()

        return json.loads(raw_text)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze logs: {str(e)}"
        )


# ─── Endpoints ─────────────────────────────────────────────────────────

@app.post("/ingest")
def ingest_logs(batch: LogBatch):
    """
    Receive and store a batch of log entries.
    Normalize timestamps and skip malformed entries.
    """

    ingested = 0

    for entry in batch.logs:

        level = entry.level.upper()

        if level not in VALID_LEVELS:
            continue

        logs.append({
            "id": str(uuid.uuid4()),
            "source": entry.source,
            "level": level,
            "message": entry.message,
            "timestamp": normalize_timestamp(entry.timestamp),
        })

        ingested += 1

    return {
        "ingested": ingested,
        "total": len(logs),
    }


@app.get("/logs")
def list_logs(
    level: Optional[str] = None,
    source: Optional[str] = None
):
    """List stored logs with optional filters."""

    result = logs

    if level:
        result = [
            l for l in result
            if l["level"] == level.upper()
        ]

    if source:
        result = [
            l for l in result
            if l["source"] == source
        ]

    return result


@app.post("/analyze")
def analyze_logs(since: Optional[str] = None):
    """
    Analyze recent logs using Ollama.
    Generates an alert if anomaly score exceeds threshold.
    """

    filtered_logs = logs

    if since:
        try:
            since_dt = datetime.fromisoformat(
                since.replace("Z", "+00:00")
            )

            filtered_logs = [
                l for l in logs
                if datetime.fromisoformat(
                    l["timestamp"].replace("Z", "+00:00")
                ) >= since_dt
            ]

        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid ISO timestamp"
            )

    if not filtered_logs:
        raise HTTPException(
            status_code=404,
            detail="No logs found for analysis"
        )

    analysis = call_ollama(filtered_logs)

    threshold = float(
        os.getenv("ANOMALY_THRESHOLD", "0.7")
    )

    if analysis.get("anomaly_score", 0) >= threshold:

        alert = {
            "id": str(uuid.uuid4()),
            "created_at": datetime.utcnow().isoformat(),
            "severity": analysis.get("severity", "UNKNOWN"),
            "root_cause": analysis.get("root_cause"),
            "recommendation": analysis.get("recommendation"),
            "anomaly_score": analysis.get("anomaly_score"),
        }

        alerts.append(alert)

        return {
            "analysis": analysis,
            "alert_generated": True,
            "alert": alert,
        }

    return {
        "analysis": analysis,
        "alert_generated": False,
    }


@app.get("/alerts")
def get_alerts(severity: Optional[str] = None):
    """
    List detected alerts with optional severity filter.
    """

    result = alerts

    if severity:
        result = [
            a for a in result
            if a["severity"].upper() == severity.upper()
        ]

    return result


@app.get("/dashboard/stats")
def dashboard_stats():
    """
    Return aggregate statistics for dashboard UI.
    """

    # Log count by level
    log_count_by_level = {
        level: 0
        for level in VALID_LEVELS
    }

    for log in logs:
        log_count_by_level[log["level"]] += 1

    # Top 5 error sources
    error_sources = Counter(
        log["source"]
        for log in logs
        if log["level"] in {"ERROR", "FATAL"}
    )

    top_error_sources = [
        {
            "source": source,
            "count": count,
        }
        for source, count in error_sources.most_common(5)
    ]

    # Alert count by severity
    alert_count_by_severity = Counter(
        alert["severity"]
        for alert in alerts
    )

    return {
        "total_logs": len(logs),
        "log_count_by_level": log_count_by_level,
        "top_5_error_sources": top_error_sources,
        "alert_count_by_severity": dict(
            alert_count_by_severity
        ),
        "total_alerts": len(alerts),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000"))
    )
```

## Example Ollama Environment Variables

```bash
export OLLAMA_URL=http://localhost:11434/api/generate
export OLLAMA_MODEL=llama3
export ANOMALY_THRESHOLD=0.7
```

## Example Analyze Request

```bash
curl -X POST \
"http://localhost:8000/analyze?since=2025-01-01T00:00:00"
```

## Example Alert Response

```json
{
  "analysis": {
    "severity": "CRITICAL",
    "root_cause": "Database connection pool exhausted",
    "recommendation": "Increase pool size and investigate connection leaks",
    "anomaly_score": 0.94
  },
  "alert_generated": true,
  "alert": {
    "id": "c1d9...",
    "created_at": "2026-06-02T12:30:11",
    "severity": "CRITICAL",
    "root_cause": "Database connection pool exhausted",
    "recommendation": "Increase pool size and investigate connection leaks",
    "anomaly_score": 0.94
  }
}
