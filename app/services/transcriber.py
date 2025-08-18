from __future__ import annotations
from pathlib import Path
import os
import shutil
import logging
import subprocess

try:
    import torch  # type: ignore
except Exception:
    torch = None  # type: ignore

logger = logging.getLogger(__name__)


def _check_ffmpeg_available() -> bool:
    """Verifica se ffmpeg está disponível no sistema.
    
    Tenta várias estratégias para encontrar ffmpeg:
    1. Procura no PATH atual
    2. Tenta usar imageio-ffmpeg
    3. Verifica se consegue executar ffmpeg
    """
    # Primeira tentativa: ffmpeg no PATH
    if shutil.which("ffmpeg"):
        try:
            # Testa se consegue executar
            result = subprocess.run(
                ["ffmpeg", "-version"], 
                capture_output=True, 
                timeout=5, 
                text=True
            )
            if result.returncode == 0:
                logger.info("ffmpeg encontrado e verificado no PATH")
                return True
        except Exception as e:
            logger.warning(f"ffmpeg encontrado no PATH mas falha ao executar: {e}")
    
    # Segunda tentativa: usar imageio-ffmpeg
    try:
        import imageio_ffmpeg
        ffexe = imageio_ffmpeg.get_ffmpeg_exe()
        if ffexe and Path(ffexe).exists():
            # Adicionar ao PATH para uso posterior
            ffdir = str(Path(ffexe).parent)
            current_path = os.environ.get("PATH", "")
            if ffdir not in current_path:
                os.environ["PATH"] = ffdir + os.pathsep + current_path
                logger.info(f"ffmpeg adicionado ao PATH via imageio-ffmpeg: {ffexe}")
            
            # Verificar se funciona
            try:
                result = subprocess.run(
                    [ffexe, "-version"], 
                    capture_output=True, 
                    timeout=5, 
                    text=True
                )
                if result.returncode == 0:
                    logger.info("ffmpeg verificado via imageio-ffmpeg")
                    return True
            except Exception as e:
                logger.warning(f"ffmpeg via imageio-ffmpeg existe mas falha ao executar: {e}")
                
    except Exception as e:
        logger.warning(f"Falha ao tentar usar imageio-ffmpeg: {e}")
    
    logger.warning("ffmpeg não disponível em nenhuma estratégia testada")
    return False


def transcribe_file(media_path: Path, model_name: str = "base") -> str:
    """Transcribe media file to text using Whisper backend.

    Priority:
    1) openai-whisper (se ffmpeg disponível)
    2) faster-whisper (fallback sempre disponível)
    Retorna texto puro.
    """
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
        # logging não deve impedir a execução
        pass

    whisper_err = None
    # Tentar openai-whisper primeiro apenas se ffmpeg estiver disponível
    if ffmpeg_available:
        try:
            import whisper  # type: ignore
            logger.info("tentando backend openai-whisper...")
            model = whisper.load_model(model_name, device=device)
            result = model.transcribe(str(media_path), fp16=(device == "cuda"))
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

        # Primeiro tentar com CUDA se disponível; se falhar, tentar CPU automaticamente
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

        segments, info = model.transcribe(str(media_path))
        text_parts = []
        for seg in segments:
            text_parts.append(seg.text)
        text = " ".join(t.strip() for t in text_parts).strip()
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