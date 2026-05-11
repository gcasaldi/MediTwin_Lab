from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.schemas import ExperimentSummary, IngestionRunResult, SimulationInput, TerminologySearchResponse
from app.core.security import require_api_key
from app.db.models import Experiment
from app.db.session import get_db
from app.services.ingestion_runner import run_ingestion
from app.services.simulation_engine import run_simulation
from app.services.terminology import search_terms

router = APIRouter(prefix="/v1")


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "meditwin-api"}


@router.post("/experiments/run", dependencies=[Depends(require_api_key)])
def run_experiment(payload: SimulationInput, db: Session = Depends(get_db)) -> dict:
    report = run_simulation(payload)

    entry = Experiment(
        report_id=report["report_meta"]["report_id"],
        patient_id=report["patient_profile"]["patient_id"],
        pathology=report["patient_profile"]["pathology"],
        benefit_score=report["assessment"]["potential_benefits"]["score"],
        risk_score=report["assessment"]["risks_and_contraindications"]["score"],
        uncertainty_score=report["assessment"]["uncertainty"]["score"],
        payload=report,
    )
    db.add(entry)
    db.commit()

    return report


@router.get("/experiments", response_model=list[ExperimentSummary])
def list_experiments(
    patient_id: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[ExperimentSummary]:
    statement = select(Experiment).order_by(Experiment.created_at.desc()).limit(limit)
    rows = db.scalars(statement).all()

    if patient_id:
        rows = [row for row in rows if row.patient_id == patient_id]

    return [
        ExperimentSummary(
            report_id=row.report_id,
            patient_id=row.patient_id,
            pathology=row.pathology,
            benefit_score=row.benefit_score,
            risk_score=row.risk_score,
            uncertainty_score=row.uncertainty_score,
            created_at=row.created_at,
        )
        for row in rows
    ]


@router.get("/experiments/{report_id}")
def get_experiment(report_id: str, db: Session = Depends(get_db)) -> dict:
    statement = select(Experiment).where(Experiment.report_id == report_id)
    row = db.scalars(statement).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return row.payload


@router.post("/ingestion/run", response_model=IngestionRunResult, dependencies=[Depends(require_api_key)])
def trigger_ingestion() -> IngestionRunResult:
    result = run_ingestion()
    return IngestionRunResult(
        run_id=result["run_id"],
        generated_at=result["generated_at"],
        source_count=result["source_count"],
        status=result["status"],
    )


@router.get("/terminologies/search", response_model=TerminologySearchResponse)
def search_terminologies(q: str = Query(min_length=2), limit: int = Query(default=20, ge=1, le=100)) -> TerminologySearchResponse:
    matches = search_terms(query=q, limit=limit)
    return TerminologySearchResponse(matches=matches)
