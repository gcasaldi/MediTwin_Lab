from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import json

from app.api.schemas import SimulationInput
from app.services.terminology import normalize_therapy_names

ROOT = Path(__file__).resolve().parents[3]
KNOWLEDGE_PATH = ROOT / "docs" / "data" / "live" / "knowledge_base.json"


@dataclass
class ScoredComponent:
    score: float
    details: list[str]


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def load_knowledge_base() -> dict:
    if not KNOWLEDGE_PATH.exists():
        return {"sources": {}}
    return json.loads(KNOWLEDGE_PATH.read_text(encoding="utf-8"))


def compute_risk(input_data: SimulationInput) -> ScoredComponent:
    score = 20.0
    details: list[str] = []

    if input_data.age >= 75:
        score += 16
        details.append("eta avanzata aumenta vulnerabilita")
    elif input_data.age >= 65:
        score += 10
        details.append("eta > 65")

    if input_data.renal_status.lower() in {"moderate", "severe", "reduced"}:
        score += 18
        details.append("funzione renale ridotta")

    if input_data.liver_status.lower() in {"moderate", "severe", "reduced"}:
        score += 16
        details.append("funzione epatica ridotta")

    if len(input_data.selected_therapies) >= 3:
        score += 14
        details.append("politerapia con rischio interazioni")
    elif len(input_data.selected_therapies) == 2:
        score += 8
        details.append("terapia combinata")

    for factor in input_data.risk_factors:
        normalized = factor.lower()
        if normalized == "smoking":
            score += 7
            details.append("fumo")
        elif normalized == "alcohol_high":
            score += 6
            details.append("consumo alcol elevato")
        elif normalized == "obesity":
            score += 8
            details.append("obesita")

    return ScoredComponent(score=clamp(score, 0, 100), details=details)


def compute_benefit(input_data: SimulationInput) -> ScoredComponent:
    score = 35.0
    details: list[str] = []
    pathology = input_data.pathology.lower()

    if "epiless" in pathology:
        score += 20
        details.append("potenziale riduzione crisi")
    if "onc" in pathology or "tum" in pathology:
        score += 15
        details.append("potenziale controllo progressione")
    if "cardio" in pathology:
        score += 12
        details.append("potenziale riduzione rischio cardiovascolare")
    if "infiam" in pathology:
        score += 10
        details.append("potenziale riduzione infiammazione")

    if len(input_data.selected_therapies) > 1:
        score += 6
        details.append("sinergia teorica combinazione")

    adherence = float(input_data.lifestyle.get("adherence", 0.8) or 0.8)
    if adherence >= 0.8:
        score += 8
        details.append("aderenza alta")
    elif adherence < 0.5:
        score -= 8
        details.append("aderenza bassa")

    return ScoredComponent(score=clamp(score, 0, 100), details=details)


def compute_interactions(selected_therapies: list[str]) -> list[dict]:
    lower = [x.strip().lower() for x in selected_therapies]
    interactions: list[dict] = []

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
                "description": "Possibile variazione efficacia da induzione enzimatica.",
            }
        )

    if len(lower) >= 3:
        interactions.append(
            {
                "severity": "medium",
                "description": "Numero elevato di farmaci con complessita farmacocinetica cumulativa.",
            }
        )

    return interactions


def compute_uncertainty(input_data: SimulationInput, knowledge_base: dict) -> float:
    uncertainty = 35.0

    if len(input_data.biomarkers) < 2:
        uncertainty += 16
    if len(input_data.selected_therapies) == 0:
        uncertainty += 25
    if input_data.liver_status.lower() == "unknown" or input_data.renal_status.lower() == "unknown":
        uncertainty += 14

    source_records = 0
    for source in knowledge_base.get("sources", {}).values():
        source_records += int(source.get("record_count", 0) or 0)

    if source_records >= 10:
        uncertainty -= 8
    if source_records == 0:
        uncertainty += 12

    return clamp(uncertainty, 0, 100)


def build_monitoring_plan(input_data: SimulationInput) -> list[str]:
    plan = [
        "funzionalita epatica (ALT, AST)",
        "funzionalita renale (eGFR, creatinina)",
        "eventi avversi teorici",
        "aderenza e qualita di vita",
    ]

    pathology = input_data.pathology.lower()
    if "epiless" in pathology:
        plan.append("frequenza e severita crisi")
    if "onc" in pathology or "tum" in pathology:
        plan.append("biomarcatori tumorali e tollerabilita")
    if "cardio" in pathology:
        plan.append("pressione arteriosa, LDL, eventi cardiovascolari")

    return plan


def run_simulation(input_data: SimulationInput) -> dict:
    knowledge_base = load_knowledge_base()
    risk = compute_risk(input_data)
    benefit = compute_benefit(input_data)
    interactions = compute_interactions(input_data.selected_therapies)
    uncertainty = compute_uncertainty(input_data, knowledge_base)
    normalized_therapies = normalize_therapy_names(input_data.selected_therapies)

    trajectory_index = clamp((benefit.score * 0.58) - (risk.score * 0.42), -100, 100)
    if trajectory_index >= 20:
        trajectory_label = "miglioramento probabile nel breve periodo"
    elif trajectory_index >= -10:
        trajectory_label = "stabilita incerta con bisogno di monitoraggio"
    else:
        trajectory_label = "rischio di peggioramento teorico"

    report_id = datetime.now(timezone.utc).strftime("exp_%Y%m%dT%H%M%SZ")
    now = datetime.now(timezone.utc).isoformat()

    return {
        "report_meta": {
            "report_id": report_id,
            "created_at": now,
            "engine": "MediTwin API Rule Engine v0.2",
            "disclaimer": "Research-only simulation. Not medical advice.",
        },
        "patient_profile": {
            "patient_id": input_data.patient_id,
            "age": input_data.age,
            "sex": input_data.sex,
            "weight_kg": input_data.weight_kg,
            "pathology": input_data.pathology,
            "liver_status": input_data.liver_status,
            "renal_status": input_data.renal_status,
            "risk_factors": input_data.risk_factors,
            "therapies_in_course": input_data.therapies_in_course,
            "selected_therapies": input_data.selected_therapies,
            "normalized_therapies": normalized_therapies,
        },
        "assessment": {
            "potential_benefits": {
                "score": round(benefit.score, 1),
                "reasons": benefit.details,
            },
            "risks_and_contraindications": {
                "score": round(risk.score, 1),
                "risk_drivers": risk.details,
                "interactions": interactions,
            },
            "evolution_scenario": {
                "trajectory_index": round(trajectory_index, 1),
                "label": trajectory_label,
                "short_horizon": "2-4 settimane virtuali",
            },
            "monitoring_parameters": build_monitoring_plan(input_data),
            "uncertainty": {
                "score": round(uncertainty, 1),
                "confidence": round(100 - uncertainty, 1),
                "notes": [
                    "l'incertezza aumenta con dati mancanti e combinazioni complesse",
                    "la simulazione non sostituisce validazione clinica reale",
                ],
            },
        },
    }
