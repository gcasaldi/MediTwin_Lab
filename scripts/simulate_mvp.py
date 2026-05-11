#!/usr/bin/env python3
"""Rule-based simulation MVP for virtual biomedical experiments.

This engine is a research prototype and does not provide medical advice.
"""

from __future__ import annotations

import argparse
import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENTS_DIR = ROOT / "data" / "experiments"
KNOWLEDGE_PATH = ROOT / "docs" / "data" / "live" / "knowledge_base.json"


@dataclass
class PatientProfile:
    patient_id: str
    age: int
    sex: str
    weight_kg: float
    pathology: str
    liver_status: str
    renal_status: str
    biomarkers: dict[str, float]
    therapies_in_course: list[str]
    risk_factors: list[str]
    lifestyle: dict[str, Any]


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def compute_risk_score(patient: PatientProfile, selected_therapies: list[str]) -> tuple[float, list[str]]:
    score = 20.0
    drivers: list[str] = []

    if patient.age >= 75:
        score += 16
        drivers.append("eta avanzata aumenta vulnerabilita farmacologica")
    elif patient.age >= 65:
        score += 10
        drivers.append("eta > 65 con possibile riduzione riserva fisiologica")

    if patient.renal_status.lower() in {"moderate", "severe", "reduced"}:
        score += 18
        drivers.append("funzionalita renale ridotta")

    if patient.liver_status.lower() in {"moderate", "severe", "reduced"}:
        score += 16
        drivers.append("funzionalita epatica ridotta")

    if len(selected_therapies) >= 3:
        score += 14
        drivers.append("politerapia con rischio di interazioni")
    elif len(selected_therapies) == 2:
        score += 8
        drivers.append("terapia combinata con complessita maggiore")

    if "smoking" in patient.risk_factors:
        score += 7
        drivers.append("fumo attivo")
    if "alcohol_high" in patient.risk_factors:
        score += 6
        drivers.append("consumo alcolico elevato")
    if "obesity" in patient.risk_factors:
        score += 8
        drivers.append("profilo metabolico a rischio")

    return clamp(score, 0, 100), drivers


def compute_benefit_score(patient: PatientProfile, selected_therapies: list[str]) -> tuple[float, list[str]]:
    base = 35.0
    reasons: list[str] = []

    pathology = patient.pathology.lower()
    if "epiless" in pathology:
        base += 20
        reasons.append("potenziale riduzione frequenza crisi")
    if "onc" in pathology or "tum" in pathology:
        base += 15
        reasons.append("possibile controllo parziale della progressione")
    if "cardio" in pathology:
        base += 12
        reasons.append("potenziale riduzione rischio di eventi cardiovascolari")
    if "infiam" in pathology:
        base += 10
        reasons.append("possibile riduzione infiammazione sistemica")

    if len(selected_therapies) > 1:
        base += 6
        reasons.append("effetto combinato potenzialmente sinergico")

    adherence = float(patient.lifestyle.get("adherence", 0.8))
    if adherence >= 0.8:
        base += 8
        reasons.append("aderenza terapeutica stimata buona")
    elif adherence < 0.5:
        base -= 8
        reasons.append("aderenza terapeutica bassa")

    return clamp(base, 0, 100), reasons


def detect_interactions(selected_therapies: list[str]) -> list[dict[str, str]]:
    interactions: list[dict[str, str]] = []
    lower = [x.strip().lower() for x in selected_therapies]

    if "valproato" in lower and "lamotrigina" in lower:
        interactions.append(
            {
                "severity": "medium-high",
                "description": "Valproato puo aumentare esposizione a lamotrigina (rischio cutaneo/sedazione).",
            }
        )

    if "carbamazepina" in lower and "clopidogrel" in lower:
        interactions.append(
            {
                "severity": "medium",
                "description": "Induzione enzimatica potenziale con possibile variazione efficacia terapeutica.",
            }
        )

    if len(lower) >= 3:
        interactions.append(
            {
                "severity": "medium",
                "description": "Numero elevato di farmaci: monitorare interazioni farmacocinetiche cumulative.",
            }
        )

    return interactions


def compute_uncertainty(patient: PatientProfile, selected_therapies: list[str], knowledge_base: dict[str, Any]) -> float:
    uncertainty = 35.0

    # Missing biomarkers increase uncertainty for trajectory predictions.
    if len(patient.biomarkers) < 2:
        uncertainty += 16
    if len(selected_therapies) == 0:
        uncertainty += 25
    if patient.liver_status.lower() == "unknown" or patient.renal_status.lower() == "unknown":
        uncertainty += 14

    source_records = 0
    for source in knowledge_base.get("sources", {}).values():
        source_records += int(source.get("record_count", 0) or 0)

    if source_records >= 10:
        uncertainty -= 8
    if source_records == 0:
        uncertainty += 12

    return clamp(uncertainty, 0, 100)


def build_report(patient: PatientProfile, selected_therapies: list[str], knowledge_base: dict[str, Any]) -> dict[str, Any]:
    risk_score, risk_drivers = compute_risk_score(patient, selected_therapies)
    benefit_score, benefit_reasons = compute_benefit_score(patient, selected_therapies)
    interactions = detect_interactions(selected_therapies)
    uncertainty_score = compute_uncertainty(patient, selected_therapies, knowledge_base)

    trajectory_index = clamp((benefit_score * 0.58) - (risk_score * 0.42), -100, 100)
    if trajectory_index >= 20:
        trajectory_label = "miglioramento probabile nel breve periodo"
    elif trajectory_index >= -10:
        trajectory_label = "stabilita incerta con bisogno di monitoraggio"
    else:
        trajectory_label = "rischio di peggioramento teorico"

    monitor = [
        "funzionalita epatica (ALT, AST)",
        "funzionalita renale (eGFR, creatinina)",
        "eventi avversi riportati dal paziente virtuale",
        "aderenza terapeutica e qualita di vita",
    ]

    if "epiless" in patient.pathology.lower():
        monitor.append("frequenza e severita crisi")
    if "onc" in patient.pathology.lower() or "tum" in patient.pathology.lower():
        monitor.append("trend biomarcatori tumorali e tollerabilita")
    if "cardio" in patient.pathology.lower():
        monitor.append("pressione arteriosa, LDL, eventi cardiovascolari")

    report_id = f"exp_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}_{uuid.uuid4().hex[:6]}"
    return {
        "report_meta": {
            "report_id": report_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "engine": "MediTwin Rule Engine MVP v0.1",
            "disclaimer": "Research-only simulation. Not medical advice.",
        },
        "patient_profile": {
            "patient_id": patient.patient_id,
            "age": patient.age,
            "sex": patient.sex,
            "weight_kg": patient.weight_kg,
            "pathology": patient.pathology,
            "liver_status": patient.liver_status,
            "renal_status": patient.renal_status,
            "risk_factors": patient.risk_factors,
            "therapies_in_course": patient.therapies_in_course,
            "selected_therapies": selected_therapies,
        },
        "assessment": {
            "potential_benefits": {
                "score": round(benefit_score, 1),
                "reasons": benefit_reasons,
            },
            "risks_and_contraindications": {
                "score": round(risk_score, 1),
                "risk_drivers": risk_drivers,
                "interactions": interactions,
            },
            "evolution_scenario": {
                "trajectory_index": round(trajectory_index, 1),
                "label": trajectory_label,
                "short_horizon": "2-4 settimane virtuali",
            },
            "monitoring_parameters": monitor,
            "uncertainty": {
                "score": round(uncertainty_score, 1),
                "confidence": round(100 - uncertainty_score, 1),
                "notes": [
                    "l'incertezza aumenta con dati mancanti e combinazioni complesse",
                    "la simulazione non sostituisce validazione clinica reale",
                ],
            },
        },
    }


def append_index(patient_id: str, report: dict[str, Any], output_path: Path) -> None:
    index_path = EXPERIMENTS_DIR / "index.json"
    index_data = load_json(index_path, {"experiments": []})
    index_data["experiments"].append(
        {
            "report_id": report["report_meta"]["report_id"],
            "patient_id": patient_id,
            "created_at": report["report_meta"]["created_at"],
            "path": str(output_path.relative_to(ROOT)).replace("\\", "/"),
            "benefit_score": report["assessment"]["potential_benefits"]["score"],
            "risk_score": report["assessment"]["risks_and_contraindications"]["score"],
            "uncertainty_score": report["assessment"]["uncertainty"]["score"],
        }
    )
    index_path.write_text(json.dumps(index_data, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run MediTwin Lab rule-based simulation MVP")
    parser.add_argument("--input", required=True, help="Path to input patient JSON")
    parser.add_argument("--output", required=False, help="Optional output file path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = (ROOT / input_path).resolve()
    if not input_path.exists():
        print(f"Input file not found: {input_path}")
        return 1

    payload = json.loads(input_path.read_text(encoding="utf-8"))
    patient = PatientProfile(
        patient_id=str(payload.get("patient_id", "virtual-patient")),
        age=int(payload.get("age", 50)),
        sex=str(payload.get("sex", "unknown")),
        weight_kg=float(payload.get("weight_kg", 70.0)),
        pathology=str(payload.get("pathology", "unknown")),
        liver_status=str(payload.get("liver_status", "unknown")),
        renal_status=str(payload.get("renal_status", "unknown")),
        biomarkers=payload.get("biomarkers", {}),
        therapies_in_course=payload.get("therapies_in_course", []),
        risk_factors=payload.get("risk_factors", []),
        lifestyle=payload.get("lifestyle", {}),
    )

    selected_therapies = payload.get("selected_therapies", [])
    if not isinstance(selected_therapies, list):
        selected_therapies = []

    knowledge_base = load_json(KNOWLEDGE_PATH, {"sources": {}})

    report = build_report(patient, selected_therapies, knowledge_base)

    EXPERIMENTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = Path(args.output) if args.output else EXPERIMENTS_DIR / f"{report['report_meta']['report_id']}.json"
    if not output_path.is_absolute():
        output_path = (ROOT / output_path).resolve()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")

    append_index(patient.patient_id, report, output_path)

    print(f"Report generated: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
