from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class SimulationInput(BaseModel):
    patient_id: str = Field(min_length=1, max_length=64)
    age: int = Field(ge=1, le=120)
    sex: str = Field(default="unknown", max_length=16)
    weight_kg: float = Field(ge=20, le=400)
    pathology: str = Field(min_length=1, max_length=120)
    liver_status: str = Field(default="unknown", max_length=24)
    renal_status: str = Field(default="unknown", max_length=24)
    selected_therapies: list[str] = Field(default_factory=list)
    therapies_in_course: list[str] = Field(default_factory=list)
    risk_factors: list[str] = Field(default_factory=list)
    biomarkers: dict[str, float] = Field(default_factory=dict)
    lifestyle: dict = Field(default_factory=dict)


class ExperimentSummary(BaseModel):
    report_id: str
    patient_id: str
    pathology: str
    benefit_score: float
    risk_score: float
    uncertainty_score: float
    created_at: datetime


class IngestionRunResult(BaseModel):
    run_id: str
    generated_at: str
    source_count: int
    status: str


class TerminologySearchResponse(BaseModel):
    matches: list[dict]
