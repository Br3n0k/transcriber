#!/usr/bin/env python3
from app.services.youtube import download_from_youtube

url = 'https://www.youtube.com/watch?v=XljPz7FWEL8'
path = download_from_youtube(url)
print('DOWNLOADED:', path)
print('SUFFIX:', path.suffix)
print('EXISTS:', path.exists())