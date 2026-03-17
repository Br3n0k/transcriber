from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from .core.config import settings
from .scripts.setup_ffmpeg import setup_ffmpeg
from .core.templates import templates  # Importa templates configurados

# Executar setup do FFmpeg se configurado
if settings.ffmpeg_auto_setup:
    setup_ffmpeg()

app = FastAPI(title=settings.app_name, debug=settings.debug)

# Mount static files
app.mount("/static", StaticFiles(directory=settings.static_dir), name="static")

from fastapi.responses import FileResponse  # noqa: E402


@app.get("/download/{filename}")
async def download(filename: str):
    file_path = settings.storage_transcriptions / filename
    return FileResponse(path=str(file_path), filename=filename, media_type="text/plain")

# Include routers (to be implemented)
from .routers import home, upload, history, websocket, library  # noqa: E402

app.include_router(home.router)
app.include_router(upload.router)
app.include_router(history.router)
app.include_router(websocket.router)
app.include_router(library.router)


@app.get("/health")
async def health():
    return {"status": "ok"}