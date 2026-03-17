from __future__ import annotations
from pathlib import Path
import logging
from typing import Literal, Optional
import yt_dlp

from ..core.config import settings

logger = logging.getLogger(__name__)

def download_from_youtube(url: str, audio_only: bool = True) -> Path:
    """Download media from YouTube using yt-dlp Python API and return local file path."""
    out_dir = settings.storage_uploads
    out_dir.mkdir(parents=True, exist_ok=True)

    # Template: title + id to avoid collisions
    out_tmpl = str(out_dir / "%(title)s-%(id)s.%(ext)s")

    ydl_opts = {
        'outtmpl': out_tmpl,
        'quiet': True,
        'no_warnings': True,
        # Prefer audio-only stream in m4a if available, else bestaudio.
        'format': 'bestaudio[ext=m4a]/bestaudio' if audio_only else 'bestvideo+bestaudio/best',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logger.info(f"Iniciando download do YouTube: {url}")
            # extract_info com download=True baixa e retorna metadados
            info = ydl.extract_info(url, download=True)
            
            # prepare_filename retorna o nome esperado do arquivo
            # Nota: se o yt-dlp fizer merge (video+audio) ou converter, o nome final pode mudar.
            # Mas como estamos pedindo bestaudio[ext=m4a], geralmente é direto.
            # Se for playlist, info é uma lista, mas aqui assumimos vídeo único ou pegamos o primeiro.
            
            if 'entries' in info:
                # É uma playlist ou resultado de busca
                info = info['entries'][0]
            
            filename = ydl.prepare_filename(info)
            path = Path(filename)
            
            if not path.exists():
                # Às vezes o yt-dlp muda a extensão se fizer pós-processamento não solicitado
                # Tentar encontrar arquivo com mesmo stem
                candidates = list(out_dir.glob(f"{path.stem}.*"))
                if candidates:
                    path = candidates[0]
            
            logger.info(f"Download concluído: {path}")
            return path
            
    except Exception as e:
        logger.exception(f"Erro ao baixar do YouTube: {e}")
        raise RuntimeError(f"Falha ao baixar do YouTube: {e}") from e
