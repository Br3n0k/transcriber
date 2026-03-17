import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys

# Importar as funções a serem testadas
# O pytest.ini deve garantir que 'app' seja importável
from app.services.transcriber import transcribe_file
from app.services.youtube import download_from_youtube
from app.services.file_manager import list_transcriptions, get_unique_stem

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
        
        # Mockar o módulo 'whisper' em sys.modules para que 'import whisper' funcione
        with patch.dict(sys.modules, {'whisper': mock_whisper}):
            # Executar
            callback = MagicMock()
            result = transcribe_file(Path("fake_audio.mp3"), model_name="base", progress_callback=callback)
        
        # Verificar
        assert result == "Texto transcodificado"
        mock_whisper.load_model.assert_called_once_with("base", device="cpu") # Assumes CPU in test env
        mock_model.transcribe.assert_called_once()
        # Verificar se callback foi chamado (pelo menos inicio e fim)
        assert callback.call_count >= 2

    @patch("app.services.transcriber._check_ffmpeg_available")
    def test_transcribe_faster_whisper(self, mock_check_ffmpeg):
        """Testa transcrição usando faster-whisper quando ffmpeg NÃO está disponível."""
        # Configurar mocks
        mock_check_ffmpeg.return_value = False
        
        mock_faster_whisper = MagicMock()
        mock_model_cls = MagicMock()
        mock_model_instance = MagicMock()
        
        # Configurar WhisperModel dentro do módulo
        mock_faster_whisper.WhisperModel = mock_model_cls
        mock_model_cls.return_value = mock_model_instance
        
        # faster-whisper retorna (segments, info)
        Segment = MagicMock()
        Segment.text = "Texto faster"
        Segment.end = 10.0
        
        Info = MagicMock()
        Info.duration = 20.0
        
        mock_model_instance.transcribe.return_value = ([Segment], Info)
        
        # Mockar o módulo 'faster_whisper' em sys.modules
        with patch.dict(sys.modules, {'faster_whisper': mock_faster_whisper}):
            # Executar
            callback = MagicMock()
            result = transcribe_file(Path("fake_audio.mp3"), model_name="small", progress_callback=callback)
        
        # Verificar
        assert result == "Texto faster"
        mock_check_ffmpeg.assert_called_once()
        # Verifica se tentou instanciar o modelo
        mock_model_cls.assert_called()
        # Verificar callback: inicio, load, seg, fim
        assert callback.call_count >= 1

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

class TestFileManager:
    @patch("app.services.file_manager.settings")
    def test_list_transcriptions(self, mock_settings):
        """Testa listagem de arquivos de transcrição."""
        # Configurar mocks
        fake_file1 = MagicMock(spec=Path)
        fake_file1.name = "file1.txt"
        fake_file1.suffix = ".txt"
        fake_file1.is_file.return_value = True
        fake_file1.stat.return_value.st_mtime = 100
        
        fake_file2 = MagicMock(spec=Path)
        fake_file2.name = "file2.txt"
        fake_file2.suffix = ".txt"
        fake_file2.is_file.return_value = True
        fake_file2.stat.return_value.st_mtime = 200
        
        mock_settings.storage_transcriptions.glob.return_value = [fake_file1, fake_file2]
        
        # Executar
        result = list_transcriptions()
        
        # Verificar (deve ordenar por data decrescente)
        assert len(result) == 2
        assert result[0] == fake_file2
        assert result[1] == fake_file1

    @patch("app.services.file_manager.settings")
    def test_get_unique_stem(self, mock_settings):
        """Testa geração de nomes únicos."""
        # Simular que 'teste.txt' já existe, mas 'teste-1.txt' não
        def exists_side_effect(path_str):
            pass
            
        # Mock mais profundo: settings.storage_transcriptions / "nome" retorna um Path
        mock_path_base = MagicMock()
        mock_settings.storage_transcriptions.__truediv__.return_value = mock_path_base
        
        # Primeiro chamado (teste.txt) existe, segundo (teste-1.txt) não existe
        mock_path_base.exists.side_effect = [True, False]
        
        # Executar
        result = get_unique_stem("teste")
        
        # Verificar
        assert result == "teste-1"
