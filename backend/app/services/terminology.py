from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TERMINOLOGY_PATH = ROOT / "data" / "terminologies" / "catalog.json"


def load_terminology_catalog() -> dict:
    if not TERMINOLOGY_PATH.exists():
        return {"systems": []}
    return json.loads(TERMINOLOGY_PATH.read_text(encoding="utf-8"))


def search_terms(query: str, limit: int = 20) -> list[dict]:
    catalog = load_terminology_catalog()
    q = query.strip().lower()
    if not q:
        return []

    matches: list[dict] = []
    for system in catalog.get("systems", []):
        for term in system.get("terms", []):
            haystack = " ".join(
                [
                    term.get("label", ""),
                    term.get("code", ""),
                    " ".join(term.get("aliases", [])),
                    system.get("name", ""),
                ]
            ).lower()
            if q in haystack:
                matches.append(
                    {
                        "system": system.get("name"),
                        "system_id": system.get("id"),
                        "code": term.get("code"),
                        "label": term.get("label"),
                        "aliases": term.get("aliases", []),
                    }
                )

    return matches[:limit]


def normalize_therapy_names(names: list[str]) -> list[dict]:
    normalized: list[dict] = []
    catalog = load_terminology_catalog()

    for value in names:
        value_lower = value.strip().lower()
        best = None
        for system in catalog.get("systems", []):
            for term in system.get("terms", []):
                aliases = [x.lower() for x in term.get("aliases", [])]
                if value_lower == term.get("label", "").lower() or value_lower in aliases:
                    best = {
                        "input": value,
                        "normalized_label": term.get("label"),
                        "code": term.get("code"),
                        "system": system.get("id"),
                    }
                    break
            if best:
                break

        if best is None:
            best = {
                "input": value,
                "normalized_label": value.strip(),
                "code": None,
                "system": "unmapped",
            }

        normalized.append(best)

    return normalized
