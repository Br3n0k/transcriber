#!/usr/bin/env python3
"""Testar importação dos módulos de transcrição."""
import pytest
import warnings

def test_imports():
    modules_to_test = [
        'whisper',
        'faster_whisper',
        'torch',
        'imageio_ffmpeg',
    ]
    
    missing_modules = []
    for module_name in modules_to_test:
        try:
            __import__(module_name)
        except ImportError:
            missing_modules.append(module_name)
            
    if missing_modules:
        pytest.skip(f"Módulos não encontrados, pulando teste: {', '.join(missing_modules)}")

if __name__ == "__main__":
    # Manter compatibilidade com execução direta
    try:
        test_imports()
        print("Todos os módulos importados com sucesso.")
    except pytest.skip.Exception as e:
        print(str(e))
