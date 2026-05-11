from __future__ import annotations

import os
from pathlib import Path


class Settings:
    def __init__(self) -> None:
        self.api_key = os.getenv("MEDITWIN_API_KEY", "change-me")
        self.db_path = Path(os.getenv("MEDITWIN_DB_PATH", "data/meditwin.db"))
        raw_origins = os.getenv("MEDITWIN_CORS_ORIGINS", "*")
        self.cors_origins = [item.strip() for item in raw_origins.split(",") if item.strip()]


settings = Settings()
