from __future__ import annotations
from pathlib import Path
import os
import logging
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from ..core.config import settings
from ..services.youtube import download_from_youtube
from ..services.transcriber import transcribe_file
from ..services.file_manager import save_upload, save_transcription, get_unique_stem
from ..core.theme import default_theme

router = APIRouter(prefix="/transcribe")

templates = Jinja2Templates(directory=str(settings.templates_dir))
# Registrar tema padrão como global para os templates
templates.env.globals["theme"] = default_theme()

logger = logging.getLogger(__name__)


@router.post("/youtube", response_class=HTMLResponse)
async def transcribe_youtube(request: Request, url: str = Form(...)):
    media_path = None
    try:
        media_path = download_from_youtube(url)
        text = transcribe_file(media_path)
        stem = get_unique_stem(media_path.name)
        out_path = save_transcription(text, stem, ".txt")
        
        # Remover o arquivo de áudio após transcrição bem-sucedida
        try:
            if media_path and media_path.exists():
                media_path.unlink()
                logger.info(f"Arquivo de áudio removido após transcrição: {media_path}")
        except Exception as cleanup_err:
            logger.warning(f"Falha ao remover arquivo de áudio {media_path}: {cleanup_err}")
        
        return templates.TemplateResponse("result.html", {"request": request, "text": text, "filename": out_path.name})
    except Exception as e:
        # Tentar limpar o arquivo em caso de erro na transcrição
        if media_path and media_path.exists():
            try:
                media_path.unlink()
                logger.info(f"Arquivo de áudio removido após erro: {media_path}")
            except Exception as cleanup_err:
                logger.warning(f"Falha ao remover arquivo de áudio após erro {media_path}: {cleanup_err}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/upload", response_class=HTMLResponse)
async def transcribe_upload(request: Request, file: UploadFile = File(...)):
    temp_path = None
    saved_path = None
    try:
        temp_path = Path(settings.storage_uploads) / file.filename
        with temp_path.open("wb") as f:
            while chunk := await file.read(1024 * 1024):
                f.write(chunk)
        saved_path = save_upload(temp_path, file.filename)
        text = transcribe_file(saved_path)
        stem = get_unique_stem(file.filename)
        out_path = save_transcription(text, stem, ".txt")
        
        # Remover o arquivo de áudio após transcrição bem-sucedida
        try:
            if saved_path and saved_path.exists():
                saved_path.unlink()
                logger.info(f"Arquivo de áudio removido após transcrição: {saved_path}")
        except Exception as cleanup_err:
            logger.warning(f"Falha ao remover arquivo de áudio {saved_path}: {cleanup_err}")
        
        context = {"request": request, "text": text, "filename": out_path.name}
        return templates.TemplateResponse("result.html", context)
    except Exception as e:
        # Tentar limpar arquivos em caso de erro na transcrição
        for path_to_clean in [temp_path, saved_path]:
            if path_to_clean and path_to_clean.exists():
                try:
                    path_to_clean.unlink()
                    logger.info(f"Arquivo removido após erro: {path_to_clean}")
                except Exception as cleanup_err:
                    logger.warning(f"Falha ao remover arquivo após erro {path_to_clean}: {cleanup_err}")
        raise HTTPException(status_code=400, detail=str(e))