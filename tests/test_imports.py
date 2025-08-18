#!/usr/bin/env python3
"""Testar importação dos módulos de transcrição."""

import sys

modules_to_test = [
    'whisper',
    'faster_whisper',
    'torch',
    'imageio_ffmpeg',
    'ctranslate2',
    'onnxruntime'
]

print("Testando importação de módulos...")
print("-" * 40)

for module_name in modules_to_test:
    try:
        __import__(module_name)
        print(f"✓ {module_name}: OK")
    except ImportError as e:
        print(f"✗ {module_name}: ImportError - {e}")
    except Exception as e:
        print(f"✗ {module_name}: {type(e).__name__} - {e}")

print("-" * 40)
print("Teste concluído.")