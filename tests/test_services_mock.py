import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys

# Importar as funções a serem testadas
# O pytest.ini deve garantir que 'app' seja importável
from app.services.transcriber import transcribe_file
from app.services.youtube import download_from_youtube

class TestTranscriber:
    @patch("app.services.transcriber._check_ffmpeg_available")
    def test_transcribe_openai_whisper(self, mock_check_ffmpeg):
        """Testa transcrição usando openai-whisper quando ffmpeg está disponível."""
        # Configurar mocks
        mock_check_ffmpeg.return_value = True
        
        mock_whisper = MagicMock()
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {"text": "Texto transcodificado"}
        mock_whisper.load_model.return_value = mock_model
        
        # Mockar o módulo 'whisper' em sys.modules
        with patch.dict(sys.modules, {'whisper': mock_whisper}):
            # Executar
            result = transcribe_file(Path("fake_audio.mp3"), model_name="base")
        
        # Verificar
        assert result == "Texto transcodificado"
        mock_whisper.load_model.assert_called_once_with("base", device="cpu") # Assumes CPU in test env
        mock_model.transcribe.assert_called_once()

    @patch("app.services.transcriber._check_ffmpeg_available")
    def test_transcribe_faster_whisper(self, mock_check_ffmpeg):
        """Testa transcrição usando faster-whisper quando ffmpeg NÃO está disponível."""
        # Configurar mocks
        mock_check_ffmpeg.return_value = False
        
        mock_faster_whisper = MagicMock()
        mock_model = MagicMock()
        # faster-whisper retorna (segments, info)
        Segment = MagicMock()
        Segment.text = "Texto faster"
        mock_model.transcribe.return_value = ([Segment], None)
        
        # Configurar WhisperModel dentro do módulo mockado
        mock_faster_whisper.WhisperModel.return_value = mock_model
        
        # Mockar o módulo 'faster_whisper' em sys.modules
        with patch.dict(sys.modules, {'faster_whisper': mock_faster_whisper}):
            # Executar
            result = transcribe_file(Path("fake_audio.mp3"), model_name="small")
        
        # Verificar
        assert result == "Texto faster"
        mock_check_ffmpeg.assert_called_once()
        # Verifica se tentou instanciar o modelo
        mock_faster_whisper.WhisperModel.assert_called()

class TestYoutube:
    @patch("app.services.youtube.subprocess.run")
    @patch("pathlib.Path.glob")
    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.stat")
    def test_download_youtube(self, mock_stat, mock_mkdir, mock_glob, mock_subprocess):
        """Testa download do YouTube mockando subprocess e sistema de arquivos."""
        
        # Configurar mocks
        mock_subprocess.return_value = MagicMock(returncode=0)
        
        # Simular arquivos encontrados
        fake_file = MagicMock(spec=Path)
        fake_file.name = "video-123.m4a"
        fake_file.suffix = ".m4a"
        fake_file.is_file.return_value = True
        fake_file.stat.return_value.st_mtime = 2000000000  # Futuro
        
        # glob retorna vazio antes, e o arquivo depois (simplificação)
        # O código original chama glob duas vezes: 'before' e 'new_candidates'
        # Vamos simular que 'new_candidates' encontra o arquivo
        mock_glob.side_effect = [
            [], # before
            [fake_file], # new_candidates
            [fake_file] # fallback
        ]
        
        # Executar
        path = download_from_youtube("https://youtube.com/watch?v=123")
        
        # Verificar
        assert path == fake_file
        mock_subprocess.assert_called_once()
        args = mock_subprocess.call_args[0][0]
        assert "yt_dlp" in args
        assert "https://youtube.com/watch?v=123" in args
