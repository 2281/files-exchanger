#!/usr/bin/env python3
"""
Простой тест для проверки работы приложения
"""

import os
import sys

# Добавляем путь к проекту в PYTHONPATH
sys.path.insert(0, '/workspace/project/files-exchanger')

def test_imports():
    """Проверка импортов"""
    try:
        print("Тест импортов...")
        
        # Импортируем основные модули
        from fastapi import FastAPI
        from src.api.files import router as files_router
        from src.api.links import router as links_router
        from src.models.file_model import FileModel
        from src.services.file_service import FileService
        from src.storage.file_storage import FileStorage
        
        print("✅ Все импорты прошли успешно")
        
        # Проверим работу сервисов
        service = FileService()
        print("✅ Сервис файлов создан успешно")
        
        storage = FileStorage()
        print("✅ Хранилище файлов создано успешно")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при импорте: {e}")
        return False

def test_structure():
    """Проверка структуры проекта"""
    try:
        print("\nТест структуры проекта...")
        
        required_dirs = ['src', 'templates', 'static', 'storage']
        for dir_path in required_dirs:
            if not os.path.exists(dir_path):
                print(f"❌ Директория {dir_path} не найдена")
                return False
            print(f"✅ Найдена директория: {dir_path}")
            
        required_files = [
            'main.py',
            'src/models/file_model.py',
            'src/services/file_service.py', 
            'src/storage/file_storage.py',
            'templates/index.html'
        ]
        
        for file_path in required_files:
            if not os.path.exists(file_path):
                print(f"❌ Файл {file_path} не найден")
                return False
            print(f"✅ Найден файл: {file_path}")
            
        print("✅ Структура проекта корректна")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при проверке структуры: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("Тестирование файлообменника")
    print("=" * 50)
    
    success = True
    success &= test_imports()
    success &= test_structure()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ Все тесты пройдены успешно!")
    else:
        print("❌ Не все тесты пройдены")
    print("=" * 50)