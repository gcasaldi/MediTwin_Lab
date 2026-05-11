from __future__ import annotations

import os
import uuid

from fastapi.testclient import TestClient

os.environ["MEDITWIN_API_KEY"] = "test-key"
os.environ["MEDITWIN_DB_PATH"] = f"/tmp/meditwin_test_{uuid.uuid4().hex}.db"

from app.main import app  # noqa: E402


def test_health() -> None:
    client = TestClient(app)
    response = client.get("/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_run_experiment_requires_key() -> None:
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
