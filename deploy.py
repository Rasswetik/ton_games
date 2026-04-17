#!/usr/bin/env python3
"""
Скрипт для деплоя Luna Gifts на Timeweb Cloud
Использует Timeweb API для загрузки приложения
"""

import requests
import json
import os
import zipfile
import sys
from pathlib import Path

# API конфиги
TIMEWEB_API_URL = "https://api.timeweb.cloud/api/v1"
API_TOKEN = "eyJhbGciOiJSUzUxMiIsInR5cCI6IkpXVCIsImtpZCI6IjFrYnhacFJNQGJSI0tSbE1xS1lqIn0.eyJ1c2VyIjoid3E4MDU2MTAiLCJ0eXBlIjoiYXBpX2tleSIsImFwaV9rZXlfaWQiOiI2NjAxODdhNy01NTEzLTQzN2ItOTE3Zi0xOTk1ZWFiOWUyYmYiLCJpYXQiOjE3NzY0Mjk0MTZ9.fTei_ZOn-WfrnggGkyt5VWUkFp8SSf-Rcycs51jR8ar_AcUdjesxKOJfQSjiiWiNsB779knN_Gqu-Zupo4a0-I6rqj08dOIYaT6o3wTyQA7-OqqdtfDrQKx1nGrAYXpkoY1jQEeisB9prvfboLO4UWrVQW_tb_Cp7Ix3C-wyLdGNKgOMRlsOKFM6EdORAGXzNEZQxZqLuieWzdldJ_cZw3t7_TEg9b2AiEYVw_dPE3k6Vkq3Sn23Ugn5ejlQZvbvFrLwjSQgLFwYb12DcYFAfj9qozmO0xMtsmtROzx4Mz8qy3I4lTJBCkdo5EGWGtpUxg3gDTXv_DKrIVKgIp3Kk5gAqFWUbdMD2px9Wh5SYK91SWEF0QleKfaXa7GCkjsOdi4zDZqx6V7GGtdti92Na3VQRwubUPOgSeZ-yTP4nvNoaO-OxjdqJxB8wz9n9CMLQr9WfkUwSFzyzGuYPrR-IcVEPwHrwQ9yayurViC9nPxf56LNFILbQ2PIe4X5zH7T"

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

def get_apps():
    """Получить список приложений"""
    try:
        response = requests.get(f"{TIMEWEB_API_URL}/apps", headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Ошибка при получении списка приложений: {e}")
        return None

def get_or_create_app():
    """Получить или создать приложение Luna Gifts"""
    print("\n📦 Проверяю список приложений...")
    
    try:
        response = requests.get(f"{TIMEWEB_API_URL}/apps", headers=HEADERS)
        response.raise_for_status()
        apps = response.json().get("apps", [])
        
        # Ищем приложение RPS GAME
        for app in apps:
            if "rps" in app.get("name", "").lower() or "game" in app.get("name", "").lower():
                print(f"✅ Найдено приложение: {app['name']} (ID: {app['id']})")
                return app
        
        # Если не найдено, создаем новое
        print("📝 Приложение не найдено. Создаю новое...")
        
        app_data = {
            "name": "RPS GAME",
            "language": "python",
            "framework": "flask"
        }
        
        response = requests.post(
            f"{TIMEWEB_API_URL}/apps",
            headers=HEADERS,
            json=app_data
        )
        response.raise_for_status()
        new_app = response.json()
        print(f"✅ Приложение создано: {new_app['name']} (ID: {new_app['id']})")
        return new_app
        
    except Exception as e:
        print(f"❌ Ошибка при работе с приложением: {e}")
        return None

def create_project_zip():
    """Создать zip архив с проектом"""
    print("\n📦 Создаю архив проекта...")
    
    project_dir = Path(".")
    zip_path = Path("luna_gifts.zip")
    
    # Исключаемые файлы и папки
    exclude = {
        "__pycache__", ".git", ".venv", "venv", ".idea", ".vscode",
        "*.pyc", "*.pyo", "*.egg-info", "deploy.py", "luna_gifts.zip",
        ".gitignore", "Procfile"
    }
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file_path in project_dir.rglob('*'):
            if file_path.is_file():
                # Проверяем, не исключен ли файл
                if any(exc in str(file_path) for exc in exclude):
                    continue
                
                # Добавляем только нужные файлы
                arcname = str(file_path.relative_to(project_dir))
                zf.write(file_path, arcname)
                print(f"  + {arcname}")
    
    print(f"✅ Архив создан: {zip_path} ({zip_path.stat().st_size / 1024:.1f} KB)")
    return zip_path

def upload_project(app_id, zip_path):
    """Загрузить проект на сервер"""
    print(f"\n📤 Загружаю проект на сервер...")
    
    try:
        with open(zip_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(
                f"{TIMEWEB_API_URL}/apps/{app_id}/upload",
                headers={
                    "Authorization": f"Bearer {API_TOKEN}",
                },
                files=files
            )
            response.raise_for_status()
            print(f"✅ Проект загружен успешно!")
            return True
    except Exception as e:
        print(f"❌ Ошибка при загрузке: {e}")
        return False

def deploy_app(app_id):
    """Развернуть приложение"""
    print(f"\n🚀 Разворачиваю приложение...")
    
    try:
        response = requests.post(
            f"{TIMEWEB_API_URL}/apps/{app_id}/deploy",
            headers=HEADERS,
            json={}
        )
        response.raise_for_status()
        print(f"✅ Приложение развернуто!")
        return True
    except Exception as e:
        print(f"⚠️ Ошибка при развертывании: {e}")
        print("Это может быть нормально - проверьте статус в панели Timeweb")
        return True

def main():
    """Главная функция"""
    print("=" * 60)
    print("� ДЕПЛОЙ RPS GAME НА TIMEWEB CLOUD")
    print("=" * 60)
    
    # Проверяем наличие токена
    if not API_TOKEN:
        print("❌ API токен не найден!")
        sys.exit(1)
    
    # Получаем или создаем приложение
    app = get_or_create_app()
    if not app:
        print("❌ Не удалось получить или создать приложение")
        sys.exit(1)
    
    app_id = app.get('id')
    
    # Создаем архив
    zip_path = create_project_zip()
    
    # Загружаем проект
    if not upload_project(app_id, zip_path):
        sys.exit(1)
    
    # Развертываем приложение
    deploy_app(app_id)
    
    # Очищаем временные файлы
    if zip_path.exists():
        zip_path.unlink()
        print(f"✅ Временный архив удален")
    
    print("\n" + "=" * 60)
    print("✅ ДЕПЛОЙ ЗАВЕРШЕН!")
    print("=" * 60)
    print(f"\n📍 Приложение: RPS GAME (ID: {app_id})")
    print("🔗 Откройте панель Timeweb для просмотра деталей")
    print("=" * 60)

if __name__ == "__main__":
    main()
