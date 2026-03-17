from typing import Dict, Any
import asyncio
import logging

logger = logging.getLogger(__name__)

class ProgressManager:
    def __init__(self):
        # Armazena o estado das tarefas: {task_id: {"status": "pending", "progress": 0, "message": "...", "result": None}}
        self.tasks: Dict[str, Dict[str, Any]] = {}
        # Armazena conexões WebSocket ativas: {task_id: websocket} (simplificado, idealmente suportaria múltiplos clientes)
        self.active_connections: Dict[str, Any] = {}

    async def create_task(self, task_id: str):
        self.tasks[task_id] = {
            "status": "pending",
            "progress": 0,
            "message": "Iniciando...",
            "result": None
        }
        logger.info(f"Tarefa criada: {task_id}")

    async def update_progress(self, task_id: str, progress: int, message: str = ""):
        if task_id in self.tasks:
            self.tasks[task_id]["progress"] = progress
            self.tasks[task_id]["status"] = "processing"
            if message:
                self.tasks[task_id]["message"] = message
            
            # Notificar via WebSocket se houver conexão ativa
            await self.notify_client(task_id)

    async def complete_task(self, task_id: str, result: Any):
        if task_id in self.tasks:
            self.tasks[task_id]["status"] = "completed"
            self.tasks[task_id]["progress"] = 100
            self.tasks[task_id]["message"] = "Concluído!"
            self.tasks[task_id]["result"] = result
            await self.notify_client(task_id)

    async def fail_task(self, task_id: str, error: str):
        if task_id in self.tasks:
            self.tasks[task_id]["status"] = "failed"
            self.tasks[task_id]["message"] = f"Erro: {error}"
            await self.notify_client(task_id)

    async def connect(self, task_id: str, websocket: Any):
        await websocket.accept()
        self.active_connections[task_id] = websocket
        # Enviar estado atual imediatamente
        if task_id in self.tasks:
            await websocket.send_json(self.tasks[task_id])

    def disconnect(self, task_id: str):
        if task_id in self.active_connections:
            del self.active_connections[task_id]

    async def notify_client(self, task_id: str):
        if task_id in self.active_connections:
            websocket = self.active_connections[task_id]
            try:
                await websocket.send_json(self.tasks[task_id])
            except Exception as e:
                logger.warning(f"Falha ao enviar update WS para {task_id}: {e}")
                self.disconnect(task_id)

progress_manager = ProgressManager()
