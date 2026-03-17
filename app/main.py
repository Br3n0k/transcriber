from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from .core.config import settings
from .core.theme import default_theme
from .scripts.setup_ffmpeg import setup_ffmpeg

# Executar setup do FFmpeg se configurado
if settings.ffmpeg_auto_setup:
    setup_ffmpeg()

app = FastAPI(title=settings.app_name, debug=settings.debug)

# Mount static files
app.mount("/static", StaticFiles(directory=settings.static_dir), name="static")

# Templates
templates = Jinja2Templates(directory=str(settings.templates_dir))

from fastapi.responses import FileResponse  # noqa: E402


@app.get("/download/{filename}")
async def download(filename: str):
    file_path = settings.storage_transcriptions / filename
    return FileResponse(path=str(file_path), filename=filename, media_type="text/plain")

# Include routers (to be implemented)
from .routers import home, upload, history  # noqa: E402

app.include_router(home.router)
app.include_router(upload.router)
app.include_router(history.router)

# Add template globals
templates.env.globals["theme"] = default_theme()


@app.get("/health")
async def health():
    return {"status": "ok"}