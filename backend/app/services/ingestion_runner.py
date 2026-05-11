from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
INGEST_SCRIPT = ROOT / "scripts" / "ingest_apis.py"
LATEST_PATH = ROOT / "data" / "ingestion" / "LATEST.json"


def run_ingestion() -> dict:
    completed = subprocess.run(
        [sys.executable, str(INGEST_SCRIPT)],
        cwd=str(ROOT),
        check=False,
        capture_output=True,
        text=True,
    )

    if completed.returncode != 0:
        return {
            "status": "error",
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "run_id": "unknown",
            "generated_at": "unknown",
            "source_count": 0,
        }

    if not LATEST_PATH.exists():
        return {
            "status": "error",
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "run_id": "unknown",
            "generated_at": "unknown",
            "source_count": 0,
        }

    payload = json.loads(LATEST_PATH.read_text(encoding="utf-8"))
    return {
        "status": "ok",
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "run_id": payload.get("run_id", "unknown"),
        "generated_at": payload.get("generated_at", "unknown"),
        "source_count": len(payload.get("sources", [])),
    }
