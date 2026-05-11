#!/usr/bin/env python3
"""Ingest public biomedical APIs and persist versioned local snapshots.

This script is intended for research prototyping only.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
INGESTION_ROOT = ROOT / "data" / "ingestion"
LIVE_ROOT = ROOT / "docs" / "data" / "live"
TIMEOUT_SECONDS = 25


@dataclass
class SourceConfig:
    id: str
    display_name: str
    category: str
    url: str
    description: str


SOURCES = [
    SourceConfig(
        id="openfda",
        display_name="openFDA Drug Event",
        category="medical",
        url="https://api.fda.gov/drug/event.json?limit=10",
        description="Adverse event metadata from openFDA public API.",
    ),
    SourceConfig(
        id="pubchem",
        display_name="PubChem Compound",
        category="chemical",
        url=(
            "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/aspirin/"
            "property/MolecularFormula,MolecularWeight,CanonicalSMILES/JSON"
        ),
        description="Representative compound properties from PubChem PUG REST.",
    ),
    SourceConfig(
        id="usda",
        display_name="USDA FoodData Central",
        category="food",
        url=(
            "https://api.nal.usda.gov/fdc/v1/foods/search?"
            + urllib.parse.urlencode({"query": "apple", "pageSize": 10, "api_key": "DEMO_KEY"})
        ),
        description="Food composition entries using FoodData Central demo key.",
    ),
]


def fetch_json(url: str) -> Any:
    request = urllib.request.Request(url, headers={"User-Agent": "MediTwin-Lab-Ingest/0.1"})
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        payload = response.read().decode(charset)
        return json.loads(payload)


def normalize(source_id: str, payload: Any) -> dict[str, Any]:
    if source_id == "openfda":
        results = payload.get("results", [])
        normalized_rows = []
        for item in results:
            patient = item.get("patient", {})
            drugs = patient.get("drug", [])
            reactions = patient.get("reaction", [])
            normalized_rows.append(
                {
                    "safetyreportid": item.get("safetyreportid"),
                    "receivedate": item.get("receivedate"),
                    "drug_count": len(drugs),
                    "reaction_terms": [r.get("reactionmeddrapt") for r in reactions if r.get("reactionmeddrapt")],
                }
            )
        return {"records": normalized_rows, "record_count": len(normalized_rows)}

    if source_id == "pubchem":
        properties = payload.get("PropertyTable", {}).get("Properties", [])
        normalized_rows = []
        for item in properties:
            normalized_rows.append(
                {
                    "cid": item.get("CID"),
                    "molecular_formula": item.get("MolecularFormula"),
                    "molecular_weight": item.get("MolecularWeight"),
                    "canonical_smiles": item.get("CanonicalSMILES") or item.get("ConnectivitySMILES"),
                }
            )
        return {"records": normalized_rows, "record_count": len(normalized_rows)}

    if source_id == "usda":
        foods = payload.get("foods", [])
        normalized_rows = []
        for item in foods:
            nutrients = item.get("foodNutrients", [])
            nutrient_names = [n.get("nutrientName") for n in nutrients if n.get("nutrientName")]
            normalized_rows.append(
                {
                    "fdc_id": item.get("fdcId"),
                    "description": item.get("description"),
                    "data_type": item.get("dataType"),
                    "nutrient_count": len(nutrients),
                    "nutrient_names": nutrient_names[:8],
                }
            )
        return {"records": normalized_rows, "record_count": len(normalized_rows)}

    return {"records": [], "record_count": 0}


def ensure_dirs() -> None:
    INGESTION_ROOT.mkdir(parents=True, exist_ok=True)
    LIVE_ROOT.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, content: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(content, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def run() -> int:
    ensure_dirs()

    run_at = datetime.now(timezone.utc)
    run_id = run_at.strftime("%Y%m%dT%H%M%SZ")
    snapshot_dir = INGESTION_ROOT / run_id
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    manifest_rows: list[dict[str, Any]] = []
    knowledge_base: dict[str, Any] = {
        "generated_at": run_at.isoformat(),
        "run_id": run_id,
        "sources": {},
    }

    for source in SOURCES:
        raw_path = snapshot_dir / f"{source.id}_raw.json"
        normalized_path = snapshot_dir / f"{source.id}_normalized.json"

        status = "ok"
        error_message = None
        record_count = 0

        try:
            payload = fetch_json(source.url)
            normalized = normalize(source.id, payload)
            record_count = normalized.get("record_count", 0)
            write_json(raw_path, payload)
            write_json(normalized_path, normalized)
            write_json(LIVE_ROOT / f"{source.id}.json", normalized)
            knowledge_base["sources"][source.id] = normalized
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            status = "error"
            error_message = str(exc)
            fallback = {
                "records": [],
                "record_count": 0,
                "error": error_message,
            }
            write_json(raw_path, {"error": error_message})
            write_json(normalized_path, fallback)
            write_json(LIVE_ROOT / f"{source.id}.json", fallback)
            knowledge_base["sources"][source.id] = fallback

        manifest_rows.append(
            {
                "source_id": source.id,
                "name": source.display_name,
                "category": source.category,
                "status": status,
                "record_count": record_count,
                "snapshot_raw": str(raw_path.relative_to(ROOT)).replace("\\", "/"),
                "snapshot_normalized": str(normalized_path.relative_to(ROOT)).replace("\\", "/"),
                "description": source.description,
                "endpoint": source.url,
                "error": error_message,
            }
        )

    manifest = {
        "run_id": run_id,
        "generated_at": run_at.isoformat(),
        "sources": manifest_rows,
    }

    write_json(snapshot_dir / "manifest.json", manifest)
    write_json(INGESTION_ROOT / "LATEST.json", manifest)
    write_json(LIVE_ROOT / "manifest.json", manifest)
    write_json(LIVE_ROOT / "knowledge_base.json", knowledge_base)

    print(f"Ingestion completed: {run_id}")
    print(f"Snapshot directory: {snapshot_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
