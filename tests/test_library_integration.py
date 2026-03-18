from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from pathlib import Path
import shutil

client = TestClient(app)

def test_library_page_render():
    # Setup: Create some dummy files to ensure the template has data to render
    settings.storage_transcriptions.mkdir(parents=True, exist_ok=True)
    settings.storage_uploads.mkdir(parents=True, exist_ok=True)
    
    t_file = settings.storage_transcriptions / "test_render.txt"
    t_file.write_text("content")
    
    a_file = settings.storage_uploads / "test_render.mp3"
    a_file.write_text("fake audio")
    
    try:
        response = client.get("/library/")
        if response.status_code != 200:
            print(f"Error content: {response.text}")
        assert response.status_code == 200
        assert "File Library" in response.text
        assert "test_render.txt" in response.text
        assert "test_render.mp3" in response.text
    finally:
        # Cleanup
        if t_file.exists(): t_file.unlink()
        if a_file.exists(): a_file.unlink()
