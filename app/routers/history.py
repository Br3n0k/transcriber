from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from ..services.file_manager import list_transcriptions
from ..core.templates import templates

router = APIRouter(prefix="/history")

@router.get("/", response_class=HTMLResponse)
async def history(request: Request):
    files = list_transcriptions()
    return templates.TemplateResponse(request=request, name="history.html", context={"files": files})