from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()

# Define o caminho base do projeto para a raiz subindo dois níveis
BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseModel):
    app_name: str = "Transcriber"
    debug: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    storage_uploads: Path = Path(os.getenv("STORAGE_UPLOADS", str(BASE_DIR / "storage" / "uploads")))
    storage_transcriptions: Path = Path(os.getenv("STORAGE_TRANSCRIPTIONS", str(BASE_DIR / "storage" / "transcriptions")))
    templates_dir: Path = Path(os.getenv("TEMPLATES_DIR", str(BASE_DIR / "app" / "templates")))
    static_dir: Path = Path(os.getenv("STATIC_DIR", str(BASE_DIR / "app" / "static")))
    
    # Auto-setup FFmpeg
    ffmpeg_auto_setup: bool = os.getenv("FFMPEG_AUTO_SETUP", "true").lower() == "true"
    
    # Whisper Settings
    whisper_model_default: str = os.getenv("WHISPER_MODEL", "base")
    # Transcription Device: 'auto' (prefer GPU), 'cuda' (force GPU), 'cpu' (force CPU)
    transcription_device: str = os.getenv("TRANSCRIPTION_DEVICE", "auto").lower()


settings = Settings()

# Ensure directories exist (apenas se forem locais, se for um storage remoto montado, pode não precisar, mas o código assume local)
# Evitar criar se for um device, por exemplo
if not str(settings.storage_uploads).startswith("/dev"): 
    settings.storage_uploads.mkdir(parents=True, exist_ok=True)
if not str(settings.storage_transcriptions).startswith("/dev"):
    settings.storage_transcriptions.mkdir(parents=True, exist_ok=True)
