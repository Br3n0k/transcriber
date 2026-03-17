import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys

# Importar as funções a serem testadas
# O pytest.ini deve garantir que 'app' seja importável
from app.services.transcriber import transcribe_file
from app.services.youtube import download_from_youtube
from app.services.file_manager import list_transcriptions, get_unique_stem, sanitize_filename

class TestTranscriber:
    @patch("app.services.transcriber._check_ffmpeg_available")
    @patch("app.services.transcriber.settings") # Mock settings
    def test_transcribe_openai_whisper(self, mock_settings, mock_check_ffmpeg):
        """Testa transcrição usando openai-whisper quando ffmpeg está disponível."""
        # Configurar mocks
        mock_check_ffmpeg.return_value = True
        mock_settings.whisper_model_default = "base"
        mock_settings.transcription_device = "cpu"
        
        mock_whisper = MagicMock()
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {"text": "Texto transcodificado"}
        mock_whisper.load_model.return_value = mock_model
        
        # Mockar o módulo 'whisper' em sys.modules para que 'import whisper' funcione
        # Como o código faz 'import whisper' dentro da função, precisamos que sys.modules['whisper'] exista
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
    @patch("app.services.transcriber.settings") # Mock settings
    def test_transcribe_faster_whisper(self, mock_settings, mock_check_ffmpeg):
        """Testa transcrição usando faster-whisper quando ffmpeg NÃO está disponível."""
        # Configurar mocks
        mock_check_ffmpeg.return_value = False
        mock_settings.whisper_model_default = "base"
        mock_settings.transcription_device = "cpu"
        
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
    @patch("app.services.youtube.Path")
    @patch("app.services.youtube.yt_dlp.YoutubeDL")
    def test_download_youtube(self, mock_ydl_class, mock_path_cls):
        """Testa download do YouTube mockando a classe YoutubeDL e Path."""
        
        # Configurar mocks
        mock_ydl_instance = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl_instance
        
        # Simular retorno do extract_info e prepare_filename
        fake_info = {"id": "123", "title": "Test Video"}
        mock_ydl_instance.extract_info.return_value = fake_info
        
        # O prepare_filename retorna uma string
        original_filename = "/tmp/Test Video-123.m4a"
        mock_ydl_instance.prepare_filename.return_value = original_filename
        
        # Configurar Mock do Path
        mock_path_instance = MagicMock()
        mock_path_cls.return_value = mock_path_instance
        
        # Configurar comportamento do Path mockado
        mock_path_instance.exists.return_value = True # Arquivo baixado existe
        mock_path_instance.name = "Test Video-123.m4a"
        mock_path_instance.stem = "Test Video-123"
        
        # Configurar with_name para retornar um novo mock
        mock_safe_path = MagicMock()
        mock_path_instance.with_name.return_value = mock_safe_path
        # O novo path deve ter o nome sanitizado
        # Test Video-123.m4a -> Test_Video-123.m4a
        
        # Executar
        result_path = download_from_youtube("https://youtube.com/watch?v=123")
        
        # Verificar
        # O resultado deve ser o path sanitizado (mock_safe_path)
        assert result_path == mock_safe_path
        
        # Verificar se with_name foi chamado com o nome sanitizado
        mock_path_instance.with_name.assert_called_once_with("Test_Video-123.m4a")
        
        # Verificar se rename/replace foi chamado
        mock_path_instance.replace.assert_called_once_with(mock_safe_path)

class TestFileManager:
    def test_sanitize_filename(self):
        """Testa a função de sanitização de nomes de arquivos."""
        # Casos de teste
        assert sanitize_filename("teste.txt") == "teste.txt"
        assert sanitize_filename("teste com espacos.txt") == "teste_com_espacos.txt"
        assert sanitize_filename("acentuação e çedilha.txt") == "acentuacao_e_cedilha.txt"
        assert sanitize_filename("MÚLTIPLOS    ESPAÇOS.txt") == "MULTIPLOS____ESPACOS.txt"
        assert sanitize_filename("invalid/chars:<>|.txt") == "invalidchars.txt"
        assert sanitize_filename("Nome do Vídeo - 123.mp3") == "Nome_do_Video_-_123.mp3"

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
        # E testar sanitização no processo
        
        # Mock mais profundo: settings.storage_transcriptions / "nome" retorna um Path
        mock_path_base = MagicMock()
        mock_settings.storage_transcriptions.__truediv__.return_value = mock_path_base
        
        # Primeiro chamado (teste_com_espaco.txt) existe, segundo (teste_com_espaco-1.txt) não existe
        mock_path_base.exists.side_effect = [True, False]
        
        # Executar com nome sujo
        result = get_unique_stem("teste com espaço")
        
        # Verificar se sanitizou e incrementou
        assert result == "teste_com_espaco-1"
