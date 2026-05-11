from __future__ import annotations

import os
from pathlib import Path

from fastapi.testclient import TestClient

os.environ["MEDITWIN_API_KEY"] = "test-key"
os.environ["MEDITWIN_DB_PATH"] = "data/test_meditwin.db"

from app.main import app  # noqa: E402


def _cleanup() -> None:
    db_file = Path("/workspaces/MediTwin_Lab/data/test_meditwin.db")
    if db_file.exists():
        db_file.unlink()


def test_health() -> None:
    _cleanup()
    client = TestClient(app)
    response = client.get("/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_run_experiment_requires_key() -> None:
    _cleanup()
    client = TestClient(app)
    payload = {
        "patient_id": "vp-test-1",
        "age": 40,
        "sex": "F",
        "weight_kg": 70,
        "pathology": "epilessia focale",
        "liver_status": "normal",
        "renal_status": "normal",
        "selected_therapies": ["valproato", "lamotrigina"],
        "risk_factors": ["smoking"],
        "biomarkers": {"egfr": 95, "alt": 24},
        "lifestyle": {"adherence": 0.8}
    }

    denied = client.post("/v1/experiments/run", json=payload)
    assert denied.status_code == 401

    accepted = client.post(
        "/v1/experiments/run",
        json=payload,
        headers={"x-api-key": "test-key"},
    )
    assert accepted.status_code == 200
    data = accepted.json()
    assert "report_meta" in data

    listed = client.get("/v1/experiments")
    assert listed.status_code == 200
    assert len(listed.json()) >= 1
