from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from ..core.config import settings
from ..services.file_manager import list_transcriptions
from ..core.theme import default_theme

router = APIRouter(prefix="/history")

templates = Jinja2Templates(directory=str(settings.templates_dir))
# Registrar tema padrão como global para os templates
templates.env.globals["theme"] = default_theme()


@router.get("/", response_class=HTMLResponse)
async def history(request: Request):
    files = list_transcriptions()
    return templates.TemplateResponse("history.html", {"request": request, "files": files})