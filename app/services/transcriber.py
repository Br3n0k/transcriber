from __future__ import annotations
from pathlib import Path
import os
import shutil
import logging
import subprocess
import sys
from typing import Callable, Optional

try:
    import torch  # type: ignore
except Exception:
    torch = None  # type: ignore

logger = logging.getLogger(__name__)


def _check_ffmpeg_available() -> bool:
    """Verifica se ffmpeg está disponível no sistema.
    
    Estratégia:
    1. Verifica se existe na pasta local .bin (criada pelo setup_ffmpeg.py) e adiciona ao PATH.
    2. Verifica se existe no PATH global.
    """
    # 1. Verificar pasta local .bin (prioridade)
    # Assumindo que .bin está na raiz do projeto (cwd ou pai de app)
    # Tenta localizar a raiz baseada no arquivo atual
    project_root = Path(__file__).resolve().parents[2]
    local_bin = project_root / ".bin"
    
    is_windows = sys.platform.startswith("win")
    exe_name = "ffmpeg.exe" if is_windows else "ffmpeg"
    local_ffmpeg = local_bin / exe_name
    
    if local_ffmpeg.exists():
        logger.info(f"FFmpeg local encontrado em: {local_ffmpeg}")
        # Adicionar ao PATH (no início para ter prioridade)
        current_path = os.environ.get("PATH", "")
        if str(local_bin) not in current_path:
            os.environ["PATH"] = str(local_bin) + os.pathsep + current_path
            logger.info("Diretório .bin adicionado ao PATH")
            
        return True

    # 2. Verificar PATH global
    if shutil.which("ffmpeg"):
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=5)
            logger.info("ffmpeg encontrado no PATH global")
            return True
        except Exception:
            pass
            
    logger.warning("ffmpeg não encontrado. Execute o script de setup ou instale manualmente.")
    return False


def transcribe_file(
    media_path: Path, 
    model_name: str = "base", 
    progress_callback: Optional[Callable[[int, str], None]] = None
) -> str:
    """Transcribe media file to text using Whisper backend.

    Priority:
    1) openai-whisper (se ffmpeg disponível)
    2) faster-whisper (fallback sempre disponível)
    Retorna texto puro.
    
    Args:
        media_path: Caminho do arquivo.
        model_name: Modelo do Whisper (base, small, medium, etc).
        progress_callback: Função para reportar progresso (0-100) e mensagem.
    """
    if progress_callback:
        progress_callback(0, "Iniciando transcrição...")

    # Verificar disponibilidade do ffmpeg de forma robusta
    ffmpeg_available = _check_ffmpeg_available()
    
    if not ffmpeg_available:
        logger.info("ffmpeg indisponível; openai-whisper será ignorado, usando apenas faster-whisper")
    else:
        logger.info("ffmpeg disponível; openai-whisper habilitado")

    # Preferir GPU (CUDA) se disponível, senão CPU
    gpu_available = bool(torch is not None and getattr(torch.cuda, "is_available", lambda: False)())
    device = "cuda" if gpu_available else "cpu"

    # Logar diagnóstico do dispositivo/ambiente
    try:
        if torch is None:
            logger.info("torch indisponível; prosseguindo com CPU/compat")
        else:
            cuda_is_avail = getattr(torch.cuda, "is_available", lambda: False)()
            cuda_ver = getattr(getattr(torch, "version", None), "cuda", None)
            if gpu_available:
                try:
                    gpu_name = torch.cuda.get_device_name(0)
                except Exception:
                    gpu_name = "(desconhecida)"
                logger.info(f"usando CUDA (GPU='{gpu_name}', torch.version.cuda={cuda_ver})")
            else:
                logger.info(f"usando CPU (torch.cuda.is_available={cuda_is_avail}, torch.version.cuda={cuda_ver})")
    except Exception:
        pass

    whisper_err = None
    # Tentar openai-whisper primeiro apenas se ffmpeg estiver disponível
    if ffmpeg_available:
        try:
            import whisper  # type: ignore
            logger.info("tentando backend openai-whisper...")
            if progress_callback:
                progress_callback(10, "Carregando modelo openai-whisper...")
            
            model = whisper.load_model(model_name, device=device)
            
            if progress_callback:
                progress_callback(20, "Processando áudio (isso pode demorar)...")
            
            # openai-whisper não tem callback nativo fácil, então pulamos direto pro fim
            result = model.transcribe(str(media_path), fp16=(device == "cuda"))
            
            if progress_callback:
                progress_callback(100, "Transcrição concluída!")
                
            logger.info(f"backend=openai-whisper device={device} fp16={device == 'cuda'} model={model_name}")
            return result.get("text", "").strip()
        except Exception as e1:
            whisper_err = e1
            logger.exception("openai-whisper falhou", exc_info=e1)
    else:
        whisper_err = RuntimeError("ffmpeg indisponível para openai-whisper")

    # Fallback para faster-whisper
    try:
        from faster_whisper import WhisperModel  # type: ignore
        logger.info("tentando backend faster-whisper...")
        
        if progress_callback:
            progress_callback(10, "Carregando modelo faster-whisper...")

        model = None
        if gpu_available:
            try:
                model = WhisperModel(model_name, device="cuda", compute_type="float16")
                logger.info("faster-whisper inicializado com CUDA (compute_type=float16)")
            except Exception as cuda_init_err:
                logger.warning("faster-whisper CUDA indisponível/sem suporte; recuando para CPU", exc_info=cuda_init_err)

        if model is None:
            model = WhisperModel(model_name, device="cpu", compute_type="int8")
            logger.info("faster-whisper inicializado com CPU (compute_type=int8)")

        if progress_callback:
            progress_callback(20, "Iniciando segmentação...")

        segments, info = model.transcribe(str(media_path))
        
        total_duration = info.duration
        text_parts = []
        
        for seg in segments:
            text_parts.append(seg.text)
            if progress_callback and total_duration > 0:
                # Progresso de 20% a 95%
                current_percent = 20 + int((seg.end / total_duration) * 75)
                current_percent = min(95, current_percent)
                progress_callback(current_percent, f"Transcrevendo: {int(seg.end)}s / {int(total_duration)}s")

        text = " ".join(t.strip() for t in text_parts).strip()
        
        if progress_callback:
            progress_callback(100, "Finalizando...")
            
        logger.info(
            f"backend=faster-whisper device={'cuda' if (gpu_available and getattr(model, 'device', 'cpu') == 'cuda') else 'cpu'} compute_type={'float16' if gpu_available else 'int8'} model={model_name}"
        )
        return text
    except Exception as e2:
        logger.exception("faster-whisper falhou", exc_info=e2)
        details = []
        if whisper_err is not None:
            details.append(f"openai-whisper: {type(whisper_err).__name__}: {whisper_err}")
        details.append(f"faster-whisper: {type(e2).__name__}: {e2}")
        raise RuntimeError(
            "Nenhum backend de transcrição disponível. Instale 'openai-whisper' ou 'faster-whisper'. "
            + " | Detalhes: " + " | ".join(details)
        ) from e2
