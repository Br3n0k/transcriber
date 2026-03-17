from pathlib import Path
from typing import Optional
import shutil
import unicodedata
import re

from ..core.config import settings


def sanitize_filename(filename: str) -> str:
    """
    Sanitize the filename by removing accents, replacing spaces with underscores,
    and removing non-alphanumeric characters (except dots and hyphens).
    """
    # Normalize unicode characters to decompose combined characters (like accents)
    nfkd_form = unicodedata.normalize('NFKD', filename)
    # Filter out non-ASCII characters (removes accents)
    only_ascii = nfkd_form.encode('ASCII', 'ignore').decode('utf-8')
    # Replace spaces with underscores
    no_spaces = only_ascii.replace(' ', '_')
    # Remove any character that is not alphanumeric, underscore, hyphen, or dot
    cleaned = re.sub(r'[^\w.-]', '', no_spaces)
    return cleaned


def save_upload(temp_file_path: Path, filename: str) -> Path:
    safe_filename = sanitize_filename(filename)
    dest = settings.storage_uploads / safe_filename
    shutil.move(str(temp_file_path), dest)
    return dest


def save_transcription(content: str, base_name: str, ext: str = ".txt") -> Path:
    # Ensure base_name is also safe, though usually it comes from get_unique_stem
    safe_base_name = sanitize_filename(base_name)
    dest = settings.storage_transcriptions / f"{safe_base_name}{ext}"
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
    # Sanitize the original name first to ensure the stem is safe
    safe_name = sanitize_filename(original_name)
    stem = Path(safe_name).stem
    i = 0
    unique = stem
    while (settings.storage_transcriptions / f"{unique}.txt").exists():
        i += 1
        unique = f"{stem}-{i}"
    return unique