from __future__ import annotations
from pathlib import Path
import logging
from typing import Optional
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from ..core.config import settings
from ..core.templates import templates
import logging
from pathlib import Path
from typing import Optional

router = APIRouter(prefix="/library")

logger = logging.getLogger(__name__)

def get_library_items():
    transcriptions_dir = settings.storage_transcriptions
    uploads_dir = settings.storage_uploads
    
    # Ensure directories exist
    if not transcriptions_dir.exists():
        transcriptions_dir.mkdir(parents=True)
    if not uploads_dir.exists():
        uploads_dir.mkdir(parents=True)

    transcription_files = sorted(
        [p for p in transcriptions_dir.glob("*.txt") if p.is_file()],
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    
    audio_files = [p for p in uploads_dir.glob("*") if p.is_file() and p.name != ".keep"]
    
    # Map stem -> audio file(s)
    # We need to handle:
    # 1. Exact stem match: video.mp4 -> video.txt
    # 2. UUID prefix: uuid_video.mp4 -> video.txt
    
    items = []
    processed_audio = set()

    for t_file in transcription_files:
        stem = t_file.stem
        related_audio = None
        
        # Strategy 1: Exact stem match
        for a_file in audio_files:
            if a_file in processed_audio:
                continue
            if a_file.stem == stem:
                related_audio = a_file
                processed_audio.add(a_file)
                break
        
        # Strategy 2: Check for uuid_stem pattern if not found
        if not related_audio:
            for a_file in audio_files:
                if a_file in processed_audio:
                    continue
                # Check if audio file ends with _{stem}.ext or just contains stem
                # Simple check: uuid_filename.ext -> filename is at the end of stem? 
                # Actually, our upload logic is: {task_id}_{filename}
                # And transcription logic is: get_unique_stem(filename) -> stem
                # So if filename was "video.mp4", audio is "uuid_video.mp4", transcription is "video.txt"
                # audio.stem is "uuid_video"
                # t.stem is "video"
                if a_file.stem.endswith(f"_{stem}"):
                    related_audio = a_file
                    processed_audio.add(a_file)
                    break

        items.append({
            "transcription": t_file.name,
            "transcription_path": str(t_file),
            "audio": related_audio.name if related_audio else None,
            "audio_path": str(related_audio) if related_audio else None,
            "date": t_file.stat().st_mtime,
            "size": t_file.stat().st_size
        })

    # Add orphaned audio files
    for a_file in audio_files:
        if a_file not in processed_audio:
             items.append({
                "transcription": None,
                "transcription_path": None,
                "audio": a_file.name,
                "audio_path": str(a_file),
                "date": a_file.stat().st_mtime,
                "size": a_file.stat().st_size
            })
            
    # Sort by date descending
    items.sort(key=lambda x: x["date"], reverse=True)
    return items

@router.get("/", response_class=HTMLResponse)
async def library_view(request: Request):
    items = get_library_items()
    return templates.TemplateResponse(request=request, name="library.html", context={"items": items})

@router.post("/delete")
async def delete_item(request: Request):
    form = await request.form()
    transcription_path = form.get("transcription_path")
    audio_path = form.get("audio_path")
    
    def safe_delete(path_str: Optional[str], allowed_dir: Path):
        if not path_str:
            return
        try:
            p = Path(path_str).resolve()
            # Security check: ensure path is within allowed directory
            if not p.is_relative_to(allowed_dir.resolve()):
                logger.warning(f"Tentativa de deletar arquivo fora do diretório permitido: {p}")
                return
            if p.exists() and p.is_file():
                p.unlink()
                logger.info(f"Arquivo deletado: {p}")
        except Exception as e:
            logger.error(f"Erro ao deletar arquivo {path_str}: {e}")

    safe_delete(transcription_path, settings.storage_transcriptions)
    safe_delete(audio_path, settings.storage_uploads)
            
    return RedirectResponse(url="/library", status_code=303)
