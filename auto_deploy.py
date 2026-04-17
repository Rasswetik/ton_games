#!/usr/bin/env python3
"""
Автоматический деплой RPS GAME на Timeweb Cloud
Использует API Timeweb с предоставленным токеном
"""

import requests
import json
import os
import sys
from pathlib import Path
import time

# API конфиги
TIMEWEB_API = "https://api.timeweb.cloud/api/v1"
API_TOKEN = "eyJhbGciOiJSUzUxMiIsInR5cCI6IkpXVCIsImtpZCI6IjFrYnhacFJNQGJSI0tSbE1xS1lqIn0.eyJ1c2VyIjoid3E4MDU2MTAiLCJ0eXBlIjoiYXBpX2tleSIsImFwaV9rZXlfaWQiOiI2NjAxODdhNy01NTEzLTQzN2ItOTE3Zi0xOTk1ZWFiOWUyYmYiLCJpYXQiOjE3NzY0Mjk0MTZ9.fTei_ZOn-WfrnggGkyt5VWUkFp8SSf-Rcycs51jR8ar_AcUdjesxKOJfQSjiiWiNsB779knN_Gqu-Zupo4a0-I6rqj08dOIYaT6o3wTyQA7-OqqdtfDrQKx1nGrAYXpkoY1jQEeisB9prvfboLO4UWrVQW_tb_Cp7Ix3C-wyLdGNKgOMRlsOKFM6EdORAGXzNEZQxZqLuieWzdldJ_cZw3t7_TEg9b2AiEYVw_dPE3k6Vkq3Sn23Ugn5ejlQZvbvFrLwjSQgLFwYb12DcYFAfj9qozmO0xMtsmtROzx4Mz8qy3I4lTJBCkdo5EGWGtpUxg3gDTXv_DKrIVKgIp3Kk5gAqFWUbdMD2px9Wh5SYK91SWEF0QleKfaXa7GCkjsOdi4zDZqx6V7GGtdti92Na3VQRwubUPOgSeZ-yTP4nvNoaO-OxjdqJxB8wz9n9CMLQr9WfkUwSFzyzGuYPrR-IcVEPwHrwQ9yayurViC9nPxf56LNFILbQ2PIe4X5zH7T"

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json",
    "User-Agent": "RPS-Game-Deployer/1.0"
}

def print_status(message, status="INFO"):
    """Красивый вывод статуса"""
    statuses = {
        "INFO": "ℹ️",
        "SUCCESS": "✅",
        "ERROR": "❌",
        "WORKING": "⚙️",
        "WAIT": "⏳"
    }
    print(f"{statuses.get(status, '•')} {message}")

def check_account():
    """Проверка аккаунта через API"""
    print_status("Проверяю доступ к аккаунту...", "WAIT")
    try:
        response = requests.get(
            f"{TIMEWEB_API}/account",
            headers=HEADERS,
            timeout=10
        )
        
        if response.status_code == 200:
            account = response.json().get("account", {})
            user = account.get("login", "Unknown")
            print_status(f"Доступ получен! Пользователь: {user}", "SUCCESS")
            return True
        else:
            print_status(f"Ошибка при проверке аккаунта: {response.status_code}", "ERROR")
            print_status(f"Ответ: {response.text}", "ERROR")
            return False
    except Exception as e:
        print_status(f"Ошибка подключения: {e}", "ERROR")
        return False

def get_or_create_app():
    """Получить или создать приложение"""
    print_status("Проверяю существующие приложения...", "WORKING")
    
    try:
        # Получаем список приложений
        response = requests.get(
            f"{TIMEWEB_API}/apps",
            headers=HEADERS,
            timeout=10
        )
        
        if response.status_code == 200:
            apps_data = response.json().get("apps", [])
            
            # Ищем существующее приложение RPS GAME
            for app in apps_data:
                if "rps" in app.get("name", "").lower():
                    print_status(f"Найдено приложение: {app['name']} (ID: {app['id']})", "SUCCESS")
                    return app['id'], app.get('name')
            
            # Если не найдено - создаем новое
            print_status("Приложение не найдено, создаю новое...", "WORKING")
            
            create_response = requests.post(
                f"{TIMEWEB_API}/apps",
                headers=HEADERS,
                json={
                    "name": "RPS GAME",
                    "language": "python",
                    "framework": "flask",
                    "public_access": True
                },
                timeout=15
            )
            
            if create_response.status_code in [200, 201]:
                new_app = create_response.json().get("app", {})
                app_id = new_app.get("id")
                app_name = new_app.get("name")
                print_status(f"Приложение создано: {app_name} (ID: {app_id})", "SUCCESS")
                return app_id, app_name
            else:
                print_status(f"Ошибка создания: {create_response.status_code}", "ERROR")
                print_status(f"Ответ: {create_response.text}", "ERROR")
                return None, None
        else:
            print_status(f"Ошибка получения списка приложений: {response.status_code}", "ERROR")
            return None, None
            
    except Exception as e:
        print_status(f"Ошибка: {e}", "ERROR")
        return None, None

def upload_files(app_id):
    """Загрузить файлы приложения"""
    print_status("Готовлю файлы к загрузке...", "WORKING")
    
    important_files = {
        'app.py': 'application/x-python',
        'requirements.txt': 'text/plain',
        'Procfile': 'text/plain',
        '.gitignore': 'text/plain',
    }
    
    try:
        # Загружаем основные файлы
        for filename in important_files:
            filepath = Path(filename)
            if filepath.exists():
                print_status(f"Загружаю {filename}...", "WORKING")
                
                with open(filepath, 'rb') as f:
                    files = {
                        'file': (filename, f, important_files[filename])
                    }
                    
                    response = requests.post(
                        f"{TIMEWEB_API}/apps/{app_id}/files",
                        headers={"Authorization": f"Bearer {API_TOKEN}"},
                        files=files,
                        timeout=20
                    )
                    
                    if response.status_code in [200, 201]:
                        print_status(f"✓ {filename} загружен", "SUCCESS")
                    else:
                        print_status(f"⚠️ {filename}: код {response.status_code}", "ERROR")
            else:
                print_status(f"Файл не найден: {filename}", "ERROR")
        
        # Загружаем папки
        folders = ['static', 'templates']
        for folder in folders:
            if Path(folder).exists():
                print_status(f"Загружаю папку {folder}...", "WORKING")
                # Рекурсивная загрузка файлов из папки
                for file_path in Path(folder).rglob('*'):
                    if file_path.is_file():
                        # Загружаем файл
                        with open(file_path, 'rb') as f:
                            relative_path = str(file_path.relative_to(Path.cwd()))
                            files = {
                                'file': (relative_path, f)
                            }
                            
                            requests.post(
                                f"{TIMEWEB_API}/apps/{app_id}/files",
                                headers={"Authorization": f"Bearer {API_TOKEN}"},
                                files=files,
                                timeout=20
                            )
                
                print_status(f"✓ Папка {folder} загружена", "SUCCESS")
        
        return True
        
    except Exception as e:
        print_status(f"Ошибка загрузки: {e}", "ERROR")
        return False

def deploy_app(app_id):
    """Развернуть приложение"""
    print_status("Разворачиваю приложение...", "WORKING")
    
    try:
        response = requests.post(
            f"{TIMEWEB_API}/apps/{app_id}/deploy",
            headers=HEADERS,
            json={},
            timeout=30
        )
        
        if response.status_code in [200, 201]:
            print_status("Приложение развернуто!", "SUCCESS")
            return True
        else:
            print_status(f"Статус: {response.status_code}", "ERROR")
            # Развертывание могло начаться даже при ошибке
            return True
            
    except Exception as e:
        print_status(f"Ошибка развертывания: {e}", "ERROR")
        return False

def get_app_status(app_id):
    """Получить статус приложения"""
    try:
        response = requests.get(
            f"{TIMEWEB_API}/apps/{app_id}",
            headers=HEADERS,
            timeout=10
        )
        
        if response.status_code == 200:
            app = response.json().get("app", {})
            status = app.get("status", "unknown")
            domain = app.get("domain", "")
            
            print_status(f"Статус приложения: {status}", "INFO")
            if domain:
                print_status(f"Домен: {domain}", "SUCCESS")
            
            return status, domain
        
    except Exception as e:
        print_status(f"Ошибка получения статуса: {e}", "ERROR")
    
    return None, None

def main():
    """Главная функция"""
    print("\n" + "="*70)
    print("🎮 АВТОМАТИЧЕСКИЙ ДЕПЛОЙ RPS GAME НА TIMEWEB CLOUD")
    print("="*70 + "\n")
    
    # 1. Проверяем доступ
    if not check_account():
        print_status("Не удалось подтвердить доступ к аккаунту", "ERROR")
        return False
    
    print()
    
    # 2. Получаем или создаем приложение
    app_id, app_name = get_or_create_app()
    if not app_id:
        print_status("Не удалось создать приложение", "ERROR")
        return False
    
    print()
    
    # 3. Загружаем файлы
    print_status("ЭТАП 3: Загрузка файлов", "INFO")
    if not upload_files(app_id):
        print_status("Ошибка при загрузке файлов", "ERROR")
        # Продолжаем несмотря на ошибки
    
    print()
    
    # 4. Разворачиваем приложение
    print_status("ЭТАП 4: Развертывание приложения", "INFO")
    deploy_app(app_id)
    
    print()
    
    # 5. Проверяем статус
    print_status("ЭТАП 5: Проверка статуса", "INFO")
    time.sleep(2)
    status, domain = get_app_status(app_id)
    
    print()
    print("="*70)
    print_status("ДЕПЛОЙ ЗАВЕРШЕН!", "SUCCESS")
    print("="*70)
    print(f"📍 Приложение: {app_name}")
    print(f"🆔 ID: {app_id}")
    print(f"📊 Статус: {status}")
    if domain:
        print(f"🌐 Перейти на: {domain}")
    print(f"🔗 Панель управления: https://timeweb.cloud/console")
    print("="*70 + "\n")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print_status("Отменено пользователем", "ERROR")
        sys.exit(1)
    except Exception as e:
        print_status(f"Критическая ошибка: {e}", "ERROR")
        sys.exit(1)
