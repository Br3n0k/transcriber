from __future__ import annotations
from pathlib import Path
import os
import logging
import uuid
import asyncio
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from ..core.config import settings
from ..services.youtube import download_from_youtube
from ..services.transcriber import transcribe_file
from ..services.file_manager import save_upload, save_transcription, get_unique_stem
from ..services.progress import progress_manager
from ..core.theme import default_theme

router = APIRouter(prefix="/transcribe")

templates = Jinja2Templates(directory=str(settings.templates_dir))
templates.env.globals["theme"] = default_theme()

logger = logging.getLogger(__name__)

async def process_transcription(task_id: str, media_path: Path, original_filename: str):
    """Função background para processar a transcrição e atualizar o progresso."""
    try:
        # Wrapper para adaptar a assinatura do callback (sync -> async bridge)
        def sync_callback(p, m):
            try:
                # Criar novo loop se necessário, pois estamos numa thread separada
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(progress_manager.update_progress(task_id, p, m))
                loop.close()
            except Exception as e:
                logger.error(f"Erro no callback de progresso: {e}")

        # Executar transcrição
        # Se passar None no model_name, usa o default do settings (base)
        text = await asyncio.to_thread(transcribe_file, media_path, None, sync_callback)
        
        stem = get_unique_stem(original_filename)
        out_path = save_transcription(text, stem, ".txt")
        
        # Limpeza
        try:
            if media_path and media_path.exists():
                media_path.unlink()
        except Exception as e:
            logger.warning(f"Erro na limpeza: {e}")

        # Atualizar status final
        await progress_manager.complete_task(task_id, {"filename": out_path.name, "text": text[:200] + "..."})

    except Exception as e:
        logger.exception(f"Erro na tarefa {task_id}")
        await progress_manager.fail_task(task_id, str(e))
        # Tentar limpar
        if media_path and media_path.exists():
            try:
                media_path.unlink()
            except:
                pass

@router.post("/youtube", response_class=HTMLResponse)
async def transcribe_youtube(request: Request, background_tasks: BackgroundTasks, url: str = Form(...)):
    try:
        # Download síncrono, mas rápido o suficiente para esperar antes de mostrar progresso
        media_path = await asyncio.to_thread(download_from_youtube, url)
        
        task_id = str(uuid.uuid4())
        await progress_manager.create_task(task_id)
        
        background_tasks.add_task(process_transcription, task_id, media_path, media_path.name)
        
        return templates.TemplateResponse(request=request, name="progress.html", context={"task_id": task_id})
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/upload", response_class=HTMLResponse)
async def transcribe_upload(request: Request, background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    try:
        task_id = str(uuid.uuid4())
        await progress_manager.create_task(task_id)
        
        # Salvar arquivo temporário
        temp_path = Path(settings.storage_uploads) / f"{task_id}_{file.filename}"
        with temp_path.open("wb") as f:
            while chunk := await file.read(1024 * 1024):
                f.write(chunk)
                
        # Iniciar background task
        background_tasks.add_task(process_transcription, task_id, temp_path, file.filename)
        
        return templates.TemplateResponse(request=request, name="progress.html", context={"task_id": task_id})
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
