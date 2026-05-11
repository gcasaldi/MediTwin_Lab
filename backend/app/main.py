from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import settings
from app.db.models import Base
from app.db.session import engine


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="MediTwin Lab API",
    version="0.2.0",
    description="Research API for in silico simulation workflows.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
