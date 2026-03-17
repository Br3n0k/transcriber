from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..services.progress import progress_manager

router = APIRouter(prefix="/ws")

@router.websocket("/progress/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    await progress_manager.connect(task_id, websocket)
    try:
        while True:
            # Manter conexão viva e escutar mensagens (embora o servidor que empurre dados)
            # O cliente pode enviar "ping" ou comandos de cancelamento no futuro
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        progress_manager.disconnect(task_id)
