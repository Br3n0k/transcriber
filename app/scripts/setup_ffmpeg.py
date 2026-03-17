#!/usr/bin/env python3
"""
Script de automação para configuração do FFmpeg.
Baixa/Configura o FFmpeg localmente usando imageio-ffmpeg como fonte confiável.
"""
import os
import sys
import shutil
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("setup_ffmpeg")

def setup_ffmpeg(force: bool = False) -> str | None:
    """
    Configura o FFmpeg localmente na pasta .bin da raiz do projeto.
    Retorna o caminho do diretório contendo o executável ffmpeg configurado.
    """
    try:
        import imageio_ffmpeg
    except ImportError:
        logger.error("imageio-ffmpeg não está instalado. Execute: pip install imageio-ffmpeg")
        return None

    # Determinar raiz do projeto (assumindo que este script está em app/scripts/)
    # Ajuste conforme a estrutura real: app/scripts/../.. = root
    project_root = Path(__file__).resolve().parents[2]
    local_bin = project_root / ".bin"
    local_bin.mkdir(exist_ok=True)

    is_windows = sys.platform.startswith("win")
    exe_name = "ffmpeg.exe" if is_windows else "ffmpeg"
    target_path = local_bin / exe_name

    if target_path.exists() and not force:
        logger.info(f"FFmpeg já configurado em: {target_path}")
        return str(local_bin)

    logger.info("Detectando FFmpeg via imageio-ffmpeg...")
    source_exe = imageio_ffmpeg.get_ffmpeg_exe()
    
    if not source_exe or not Path(source_exe).exists():
        logger.error("Falha ao obter executável do imageio-ffmpeg.")
        return None

    logger.info(f"Fonte encontrada: {source_exe}")
    
    try:
        shutil.copy(source_exe, target_path)
        # Garantir permissão de execução em Unix
        if not is_windows:
            target_path.chmod(target_path.stat().st_mode | 0o111)
            
        logger.info(f"FFmpeg instalado com sucesso em: {target_path}")
        return str(local_bin)
    except Exception as e:
        logger.error(f"Erro ao copiar FFmpeg: {e}")
        return None

if __name__ == "__main__":
    setup_ffmpeg(force=True)
