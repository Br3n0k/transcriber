from __future__ import annotations
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Literal, Optional
import time

from ..core.config import settings


def download_from_youtube(url: str, audio_only: bool = True) -> Path:
    """Download media from YouTube using yt-dlp and return local file path.

    If audio_only=True, prefer direct audio (m4a) without postprocessing to avoid ffmpeg.
    """
    out_dir = settings.storage_uploads
    out_dir.mkdir(parents=True, exist_ok=True)

    # Template: title + id to avoid collisions
    out_tmpl = str(out_dir / "%(title)s-%(id)s.%(ext)s")

    # Build command
    cmd = [
        sys.executable,
        "-m",
        "yt_dlp",
        "-o",
        out_tmpl,
        url,
    ]
    if audio_only:
        # Prefer an audio-only stream in m4a if available, else bestaudio.
        # Avoid --extract-audio to not require ffmpeg at runtime.
        cmd.extend(["-f", "bestaudio[ext=m4a]/bestaudio"])
    else:
        cmd.extend(["-f", "bestvideo+bestaudio/best"]) 

    # Snapshot before download
    before = {p.name for p in out_dir.glob("*") if p.is_file()}
    started_at = time.time()

    subprocess.run(cmd, check=True)

    # Allowed media extensions
    allowed_exts = {".mp3", ".m4a", ".mp4", ".webm", ".wav", ".mkv", ".ogg", ".flac", ".m4v"}

    # Prefer files created after we started and not present before
    new_candidates = [
        p for p in out_dir.glob("*")
        if p.is_file()
        and p.suffix.lower() in allowed_exts
        and (p.name not in before or p.stat().st_mtime >= started_at - 1)
    ]

    if new_candidates:
        return max(new_candidates, key=lambda p: p.stat().st_mtime)

    # Fallback: pick most recent media file in the directory (ignore .keep and non-media)
    candidates = sorted(
        [p for p in out_dir.glob("*") if p.is_file() and p.suffix.lower() in allowed_exts],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        raise RuntimeError("Falha ao baixar o conteúdo do YouTube (nenhum arquivo de mídia encontrado).")
    return candidates[0]