import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from app.routers.library import get_library_items

@patch("app.routers.library.settings")
def test_get_library_items_correlation(mock_settings):
    # Setup mocks
    mock_transcriptions_dir = MagicMock(spec=Path)
    mock_uploads_dir = MagicMock(spec=Path)
    
    mock_settings.storage_transcriptions = mock_transcriptions_dir
    mock_settings.storage_uploads = mock_uploads_dir
    
    # Mock files
    # Case 1: Exact match
    t1 = MagicMock(spec=Path)
    t1.name = "video1.txt"
    t1.stem = "video1"
    t1.is_file.return_value = True
    t1.stat.return_value.st_mtime = 1000
    t1.stat.return_value.st_size = 500
    t1.__str__.return_value = "/path/to/video1.txt"

    a1 = MagicMock(spec=Path)
    a1.name = "video1.mp4"
    a1.stem = "video1"
    a1.is_file.return_value = True
    a1.stat.return_value.st_mtime = 1000
    a1.stat.return_value.st_size = 10000
    a1.__str__.return_value = "/path/to/video1.mp4"
    
    # Case 2: UUID match
    t2 = MagicMock(spec=Path)
    t2.name = "video2.txt"
    t2.stem = "video2"
    t2.is_file.return_value = True
    t2.stat.return_value.st_mtime = 900
    t2.stat.return_value.st_size = 500
    t2.__str__.return_value = "/path/to/video2.txt"

    a2 = MagicMock(spec=Path)
    a2.name = "uuid-123_video2.mp4"
    a2.stem = "uuid-123_video2"
    a2.is_file.return_value = True
    a2.stat.return_value.st_mtime = 900
    a2.stat.return_value.st_size = 10000
    a2.__str__.return_value = "/path/to/uuid-123_video2.mp4"
    
    # Case 3: Orphan Transcription
    t3 = MagicMock(spec=Path)
    t3.name = "orphan.txt"
    t3.stem = "orphan"
    t3.is_file.return_value = True
    t3.stat.return_value.st_mtime = 800
    t3.stat.return_value.st_size = 500
    t3.__str__.return_value = "/path/to/orphan.txt"

    # Case 4: Orphan Audio
    a4 = MagicMock(spec=Path)
    a4.name = "orphan_audio.mp3"
    a4.stem = "orphan_audio"
    a4.is_file.return_value = True
    a4.stat.return_value.st_mtime = 700
    a4.stat.return_value.st_size = 10000
    a4.__str__.return_value = "/path/to/orphan_audio.mp3"

    mock_transcriptions_dir.glob.return_value = [t1, t2, t3]
    mock_uploads_dir.glob.return_value = [a1, a2, a4]
    
    # Execute
    items = get_library_items()
    
    # Verify
    assert len(items) == 4
    
    # Check Case 1 (Exact Match)
    item1 = next(i for i in items if i["transcription"] == "video1.txt")
    assert item1["audio"] == "video1.mp4"
    
    # Check Case 2 (UUID Match)
    item2 = next(i for i in items if i["transcription"] == "video2.txt")
    assert item2["audio"] == "uuid-123_video2.mp4"
    
    # Check Case 3 (Orphan Transcription)
    item3 = next(i for i in items if i["transcription"] == "orphan.txt")
    assert item3["audio"] is None
    
    # Check Case 4 (Orphan Audio)
    item4 = next(i for i in items if i["audio"] == "orphan_audio.mp3")
    assert item4["transcription"] is None
