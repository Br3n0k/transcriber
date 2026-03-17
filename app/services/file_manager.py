from pathlib import Path
from typing import Optional
import shutil

from ..core.config import settings


def save_upload(temp_file_path: Path, filename: str) -> Path:
    dest = settings.storage_uploads / filename
    shutil.move(str(temp_file_path), dest)
    return dest


def save_transcription(content: str, base_name: str, ext: str = ".txt") -> Path:
    dest = settings.storage_transcriptions / f"{base_name}{ext}"
    dest.write_text(content, encoding="utf-8")
    return dest


def list_transcriptions() -> list[Path]:
    # List only actual transcription files (e.g., .txt) and ignore placeholders like .keep
    allowed_exts = {".txt"}
    return sorted(
        [
            p
            for p in settings.storage_transcriptions.glob("*")
            if p.is_file() and p.suffix.lower() in allowed_exts
        ],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )


def get_unique_stem(original_name: str) -> str:
    stem = Path(original_name).stem
    i = 0
    unique = stem
    while (settings.storage_transcriptions / f"{unique}.txt").exists():
        i += 1
        unique = f"{stem}-{i}"
    return unique