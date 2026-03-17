from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from ..core.config import settings
from ..core.theme import default_theme

router = APIRouter()

templates = Jinja2Templates(directory=str(settings.templates_dir))
# Registrar tema padrão como global para os templates
templates.env.globals["theme"] = default_theme()


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")