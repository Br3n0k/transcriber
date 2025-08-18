from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseModel):
    app_name: str = "Transcriber"
    debug: bool = os.getenv("DEBUG", "true").lower() == "true"
    storage_uploads: Path = BASE_DIR / "storage" / "uploads"
    storage_transcriptions: Path = BASE_DIR / "storage" / "transcriptions"
    templates_dir: Path = BASE_DIR / "app" / "templates"
    static_dir: Path = BASE_DIR / "app" / "static"


settings = Settings()

# Ensure directories exist
settings.storage_uploads.mkdir(parents=True, exist_ok=True)
settings.storage_transcriptions.mkdir(parents=True, exist_ok=True)