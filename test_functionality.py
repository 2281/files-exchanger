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
        response = requests.post('http://localhost:8001/api/files/upload', files=files)
        print(f"POST /api/files/upload: {response.status_code}")
        if response.status_code == 200:
            print("Файл загружен успешно")
            # Получим информацию о файле для скачивания
            file_info = response.json()
            if 'file' in file_info and 'id' in file_info['file']:
                file_id = file_info['file']['id']
                print(f"ID загруженного файла: {file_id}")
                
                # Теперь попробуем скачать файл
                download_url = f'http://localhost:8001/api/files/download/{file_id}'
                print(f"Попытка скачивания файла по URL: {download_url}")
                
                download_response = requests.get(download_url)
                print(f"GET /api/files/download/{file_id}: {download_response.status_code}")
                
                if download_response.status_code == 200:
                    # Сохраним скачанный файл для проверки
                    with open('downloaded_test_file.txt', 'wb') as f:
                        f.write(download_response.content)
                    print("Файл успешно скачан")
                    
                    # Проверим содержимое
                    with open('downloaded_test_file.txt', 'r') as f:
                        downloaded_content = f.read()
                    if downloaded_content == test_file_content:
                        print("Содержимое файла совпадает")
                    else:
                        print("Содержимое файла не совпадает!")
                        
                    # Очистим скачанный файл
                    os.remove('downloaded_test_file.txt')
                else:
                    print(f"Ошибка скачивания файла: {download_response.status_code}")
                    if download_response.status_code == 404:
                        print("Файл не найден (возможно ошибка в пути)")
                    elif download_response.status_code == 500:
                        print("Ошибка сервера при скачивании")
                        
        else:
            print("Ошибка загрузки файла:", response.json())
            
    except Exception as e:
        print(f"Ошибка при тестировании: {e}")
    
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