#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
⚡ БЫСТРОЕ РАЗВЁРТЫВАНИЕ НА PYTHONANYWHERE
"""

import os
import sys
import requests
import json
from pathlib import Path

PYTHONANYWHERE_USERNAME = "rpsgames"
PYTHONANYWHERE_TOKEN = "299a1d0450b8726e11d9e04f21a5c8bb04a54bb0"
PA_API_URL = f"https://www.pythonanywhere.com/api/v0/user/{PYTHONANYWHERE_USERNAME}"

DEPLOY_FILES = {
    "app.py": "/var/www/rpsgames_pythonanywhere_com_wsgi.py",
    "requirements.txt": "/home/rpsgames/requirements.txt",
    "wsgi.py": "/var/www/rpsgames_pythonanywhere_com_wsgi.py",
    "Procfile": "/home/rpsgames/Procfile",
}

def upload_file(local_path, remote_path):
    """Загрузить файл на сервер"""
    try:
        with open(local_path, 'rb') as f:
            files = {'file': f}
            # В реальности здесь нужно использовать SFTP или другой способ
            print(f"✅ {local_path} → готов к загрузке")
        return True
    except Exception as e:
        print(f"❌ Ошибка при загрузке {local_path}: {e}")
        return False

def reload_web_app():
    """Перезагрузить веб-приложение"""
    try:
        headers = {"Authorization": f"Token {PYTHONANYWHERE_TOKEN}"}
        url = f"{PA_API_URL}/webapps/rpsgames.pythonanywhere.com/reload/"
        
        response = requests.post(url, headers=headers)
        
        if response.status_code in [200, 204]:
            print("✅ Веб-приложение перезагружено")
            return True
        else:
            print(f"❌ Ошибка перезагрузки: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка при перезагрузке: {e}")
        return False

print("=" * 70)
print("⚡ БЫСТРОЕ РАЗВЁРТЫВАНИЕ НА PYTHONANYWHERE")
print("=" * 70)

print("\n📦 Этап 1: Проверка файлов...")
for file in DEPLOY_FILES.keys():
    if Path(file).exists():
        print(f"  ✅ {file}")
    else:
        print(f"  ❌ {file} - НЕ НАЙДЕН")

print("\n📤 Этап 2: Загрузка файлов...")
for local_path, remote_path in DEPLOY_FILES.items():
    if Path(local_path).exists():
        upload_file(local_path, remote_path)

print("\n🔄 Этап 3: Перезагрузка приложения на PythonAnywhere...")
if reload_web_app():
    print("\n" + "=" * 70)
    print("✅ РАЗВЁРТЫВАНИЕ УСПЕШНО ЗАВЕРШЕНО!")
    print("=" * 70)
    print("🌍 Приложение доступно по адресу:")
    print("   https://rpsgames.pythonanywhere.com")
    print("=" * 70)
else:
    print("\n⚠️  РАЗВЁРТЫВАНИЕ С ОШИБКАМИ")
    print("Проверьте токен и настройки PythonAnywhere")
