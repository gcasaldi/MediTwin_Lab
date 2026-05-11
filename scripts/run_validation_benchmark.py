#!/usr/bin/env python3
"""Run synthetic benchmark scenarios against the MVP rule engine."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.api.schemas import SimulationInput  # noqa: E402
from app.services.simulation_engine import run_simulation  # noqa: E402

VALIDATION_DIR = ROOT / "data" / "validation"


SCENARIOS = [
    {
        "name": "epilepsy_combo_balanced",
        "input": {
            "patient_id": "bench-001",
            "age": 35,
            "sex": "F",
            "weight_kg": 64,
            "pathology": "epilessia focale",
            "liver_status": "mild",
            "renal_status": "normal",
            "selected_therapies": ["valproato", "lamotrigina"],
            "therapies_in_course": ["levetiracetam"],
            "risk_factors": ["smoking"],
            "biomarkers": {"egfr": 95, "alt": 33},
            "lifestyle": {"adherence": 0.84}
        }
    },
    {
        "name": "oncology_polytherapy_high_risk",
        "input": {
            "patient_id": "bench-002",
            "age": 74,
            "sex": "M",
            "weight_kg": 78,
            "pathology": "oncologia avanzata",
            "liver_status": "moderate",
            "renal_status": "moderate",
            "selected_therapies": ["farmaco-a", "farmaco-b", "farmaco-c"],
            "therapies_in_course": ["farmaco-d"],
            "risk_factors": ["obesity", "alcohol_high"],
            "biomarkers": {"egfr": 42, "alt": 81},
            "lifestyle": {"adherence": 0.62}
        }
    },
    {
        "name": "cardio_low_data_high_uncertainty",
        "input": {
            "patient_id": "bench-003",
            "age": 59,
            "sex": "F",
            "weight_kg": 70,
            "pathology": "rischio cardiovascolare",
            "liver_status": "unknown",
            "renal_status": "unknown",
            "selected_therapies": ["clopidogrel"],
            "therapies_in_course": [],
            "risk_factors": ["smoking"],
            "biomarkers": {},
            "lifestyle": {"adherence": 0.4}
        }
    }
]


def run_benchmark() -> dict:
    records: list[dict] = []

    for scenario in SCENARIOS:
        payload = SimulationInput(**scenario["input"])
        report = run_simulation(payload)
        records.append(
            {
                "scenario": scenario["name"],
                "report_id": report["report_meta"]["report_id"],
                "benefit_score": report["assessment"]["potential_benefits"]["score"],
                "risk_score": report["assessment"]["risks_and_contraindications"]["score"],
                "uncertainty_score": report["assessment"]["uncertainty"]["score"],
                "trajectory": report["assessment"]["evolution_scenario"]["label"],
            }
        )

    aggregate = {
        "mean_benefit": round(sum(r["benefit_score"] for r in records) / len(records), 2),
        "mean_risk": round(sum(r["risk_score"] for r in records) / len(records), 2),
        "mean_uncertainty": round(sum(r["uncertainty_score"] for r in records) / len(records), 2),
    }

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "benchmark_version": "mvp-rule-engine-v0.2",
        "scenario_count": len(records),
        "aggregate": aggregate,
        "records": records,
        "disclaimer": "Synthetic benchmark for research only. Not clinical validation.",
    }


def main() -> int:
    VALIDATION_DIR.mkdir(parents=True, exist_ok=True)
    output = run_benchmark()
    timestamp = datetime.now(timezone.utc).strftime("benchmark_%Y%m%dT%H%M%SZ.json")
    output_path = VALIDATION_DIR / timestamp
    output_path.write_text(json.dumps(output, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    latest_path = VALIDATION_DIR / "LATEST.json"
    latest_path.write_text(json.dumps(output, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    print(f"Benchmark completed: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
