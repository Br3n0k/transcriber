#!/usr/bin/env python3
from pathlib import Path
from app.services.youtube import download_from_youtube
from app.services.transcriber import transcribe_file

url = 'https://www.youtube.com/watch?v=XljPz7FWEL8'
path = download_from_youtube(url)
print('FILE:', path)

try:
    text = transcribe_file(Path(path))
    print('OK. First 300 chars:')
    print(text[:300])
except Exception as e:
    print('ERR:', type(e).__name__, e)