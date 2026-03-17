#!/usr/bin/env python3
"""Testar importação dos módulos de transcrição."""
import pytest

def test_imports():
    modules_to_test = [
        'whisper',
        'faster_whisper',
        'torch',
        'imageio_ffmpeg',
        # 'ctranslate2', # Dependencies of faster_whisper, might not be direct imports for the app
        # 'onnxruntime'
    ]
    
    errors = []
    for module_name in modules_to_test:
        try:
            __import__(module_name)
        except ImportError as e:
            errors.append(f"{module_name}: {e}")
            
    if errors:
        pytest.fail(f"Falha ao importar módulos: {', '.join(errors)}")

if __name__ == "__main__":
    # Manter compatibilidade com execução direta
    test_imports()
    print("Todos os módulos importados com sucesso.")
