#!/usr/bin/env python3
"""
Тестирование функциональности файлового обменника
"""

import os
import sys
import requests
import time

# Добавим путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_endpoints():
    """Проверка всех эндпоинтов"""
    
    # Проверим запуск сервера
    try:
        response = requests.get('http://localhost:8001/api/files')
        print(f"GET /api/files: {response.status_code}")
        if response.status_code == 200:
            print("Список файлов:", response.json())
        else:
            print("Ошибка получения списка файлов")
            
    except requests.exceptions.ConnectionError:
        print("Сервер не запущен или недоступен")
        return

def test_upload_download():
    """Тест загрузки и скачивания файла"""
    
    # Создадим тестовый файл
    test_file_content = "Это тестовый файл для проверки функциональности"
    with open('test_file.txt', 'w') as f:
        f.write(test_file_content)
    
    try:
        # Попробуем загрузить файл  
        files = {'file': open('test_file.txt', 'rb')}
        response = requests.post('http://localhost:8001/api/upload', files=files)
        print(f"POST /api/upload: {response.status_code}")
        if response.status_code == 200:
            print("Файл загружен успешно")
        else:
            print("Ошибка загрузки файла:", response.json())
            
    except Exception as e:
        print(f"Ошибка при загрузке файла: {e}")
    
    # Очистим тестовый файл
    try:
        os.remove('test_file.txt')
    except:
        pass

if __name__ == "__main__":
    print("Тестирование файлового обменника")
    print("=" * 40)
    
    test_endpoints()
    print()
    test_upload_download()