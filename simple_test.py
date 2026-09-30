#!/usr/bin/env python3
"""
Простой тест для проверки существующей функциональности
"""

import os
import sys
import unittest

# Добавим путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_structure():
    """Проверка структуры проекта"""
    
    print("=== Проверка структуры проекта ===")
    
    # Проверяем наличие директорий
    required_dirs = ['src', 'templates', 'static', 'storage']
    for dir_name in required_dirs:
        if os.path.exists(dir_name):
            print(f"✓ Директория {dir_name} существует")
        else:
            print(f"✗ Директория {dir_name} отсутствует")
    
    # Проверяем наличие необходимых файлов
    required_files = ['main.py', 'requirements.txt']
    for file_name in required_files:
        if os.path.exists(file_name):
            print(f"✓ Файл {file_name} существует")
        else:
            print(f"✗ Файл {file_name} отсутствует")
    
    # Проверяем наличие основных компонентов в src
    src_dirs = ['src/api', 'src/models', 'src/services', 'src/storage']
    for dir_name in src_dirs:
        if os.path.exists(dir_name):
            print(f"✓ Директория {dir_name} существует")
        else:
            print(f"✗ Директория {dir_name} отсутствует")

def test_imports():
    """Проверка импортов"""
    print("\n=== Проверка импортов ===")
    
    try:
        import main
        print("✓ Импорт main.py успешен")
    except Exception as e:
        print(f"✗ Ошибка импорта main.py: {e}")
    
    try:
        from src.models.file_model import FileModel
        print("✓ Импорт FileModel успешен")
    except Exception as e:
        print(f"✗ Ошибка импорта FileModel: {e}")
        
    try:
        from src.storage.file_storage import FileStorage 
        print("✓ Импорт FileStorage успешен")
    except Exception as e:
        print(f"✗ Ошибка импорта FileStorage: {e}")

def test_api_endpoints():
    """Поиск API эндпоинтов"""
    print("\n=== Поиск API эндпоинтов ===")
    
    # Проверяем, что есть нужные файлы
    api_files = [
        'src/api/files.py',
        'src/api/links.py'
    ]
    
    for file_path in api_files:
        if os.path.exists(file_path):
            print(f"✓ API файл {file_path} существует")
        else:
            print(f"✗ API файл {file_path} отсутствует")

if __name__ == "__main__":
    test_structure()
    test_imports()
    test_api_endpoints()
    print("\n=== Тест завершен ===")