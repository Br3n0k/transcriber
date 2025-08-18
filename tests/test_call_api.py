#!/usr/bin/env python3
import urllib.request
import urllib.parse

url = 'http://127.0.0.1:8000/transcribe/youtube'
body = urllib.parse.urlencode({'url': 'https://www.youtube.com/watch?v=XljPz7FWEL8'}).encode()
req = urllib.request.Request(url, data=body, method='POST', headers={'Content-Type': 'application/x-www-form-urlencoded'})

try:
    with urllib.request.urlopen(req) as resp:
        print('STATUS', resp.getcode())
        print(resp.read().decode('utf-8', errors='replace'))
except urllib.error.HTTPError as e:
    print('STATUS', e.code)
    try:
        print(e.read().decode('utf-8', errors='replace'))
    except Exception as ie:
        print(f"<no-body> {ie}")
except Exception as ex:
    print('ERROR', type(ex).__name__, ex)