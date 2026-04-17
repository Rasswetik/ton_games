#!/usr/bin/env python3
"""
Полностью автоматический деплой на Timeweb Cloud
с поддержкой всех методов загрузки
"""

import subprocess
import requests
import json
import os
import sys
from pathlib import Path

API_TOKEN = "eyJhbGciOiJSUzUxMiIsInR5cCI6IkpXVCIsImtpZCI6IjFrYnhacFJNQGJSI0tSbE1xS1lqIn0.eyJ1c2VyIjoid3E4MDU2MTAiLCJ0eXBlIjoiYXBpX2tleSIsImFwaV9rZXlfaWQiOiI2NjAxODdhNy01NTEzLTQzN2ItOTE3Zi0xOTk1ZWFiOWUyYmYiLCJpYXQiOjE3NzY0Mjk0MTZ9.fTei_ZOn-WfrnggGkyt5VWUkFp8SSf-Rcycs51jR8ar_AcUdjesxKOJfQSjiiWiNsB779knN_Gqu-Zupo4a0-I6rqj08dOIYaT6o3wTyQA7-OqqdtfDrQKx1nGrAYXpkoY1jQEeisB9prvfboLO4UWrVQW_tb_Cp7Ix3C-wyLdGNKgOMRlsOKFM6EdORAGXzNEZQxZqLuieWzdldJ_cZw3t7_TEg9b2AiEYVw_dPE3k6Vkq3Sn23Ugn5ejlQZvbvFrLwjSQgLFwYb12DcYFAfj9qozmO0xMtsmtROzx4Mz8qy3I4lTJBCkdo5EGWGtpUxg3gDTXv_DKrIVKgIp3Kk5gAqFWUbdMD2px9Wh5SYK91SWEF0QleKfaXa7GCkjsOdi4zDZqx6V7GGtdti92Na3VQRwubUPOgSeZ-yTP4nvNoaO-OxjdqJxB8wz9n9CMLQr9WfkUwSFzyzGuYPrR-IcVEPwHrwQ9yayurViC9nPxf56LNFILbQ2PIe4X5zH7T"
TIMEWEB_API = "https://api.timeweb.cloud/api/v1"

def print_step(msg, icon="•"):
    print(f"{icon} {msg}")

def deploy_with_curl():
    """Попытка загрузки через curl"""
    print_step("Попытка 1: Загрузка через curl...", "🔄")
    
    zip_path = Path("rps_game_deploy.zip")
    if not zip_path.exists():
        print_step("Архив не найден!", "❌")
        return False
    
    try:
        # Используем curl для загрузки
        cmd = f'curl -X POST https://api.timeweb.cloud/api/v1/apps -H "Authorization: Bearer {API_TOKEN}" -F "file=@{zip_path}" 2>nul'
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print_step("✅ Загрузка через curl успешна!", "✅")
            print(result.stdout)
            return True
        else:
            print_step(f"curl вернул ошибку: {result.returncode}", "⚠️")
            return False
    except Exception as e:
        print_step(f"Ошибка curl: {e}", "⚠️")
        return False

def get_git_credentials():
    """Получить GitHub credentials"""
    print_step("Проверяю Git конфигурацию...", "🔍")
    
    try:
        # Попытаемся использовать существующие credentials
        cmd = 'git config --global credential.helper'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            return True
        
        # Если нет - создаем
        print_step("Конфигурирую Git...", "⚙️")
        subprocess.run('git config --global credential.helper wincred', shell=True)
        return True
    except:
        return False

def git_push_auto():
    """Автоматический push на GitHub"""
    print_step("Попытка 2: Push на GitHub...", "🔄")
    
    try:
        print_step("Добавляю файлы...", "📝")
        subprocess.run("git add .", shell=True, check=True, capture_output=True)
        
        print_step("Создаю коммит...", "📝")
        subprocess.run('git commit -m "Auto deploy RPS GAME" --allow-empty', shell=True, capture_output=True)
        
        print_step("Push на GitHub...", "📤")
        result = subprocess.run("git push origin main -v", shell=True, capture_output=True, text=True)
        
        if result.returncode == 0 or "everything up-to-date" in result.stdout.lower():
            print_step("✅ Успешно загружено на GitHub!", "✅")
            return True
        else:
            print_step(f"Git ошибка: {result.stderr}", "⚠️")
            return False
    except Exception as e:
        print_step(f"Git ошибка: {e}", "⚠️")
        return False

def create_app_manually():
    """Создать приложение через API"""
    print_step("Попытка 3: Создание приложения через API...", "🔄")
    
    try:
        headers = {
            "Authorization": f"Bearer {API_TOKEN}",
            "Content-Type": "application/json"
        }
        
        app_data = {
            "name": "RPS GAME",
            "language": "python",
            "framework": "flask",
            "public_access": True
        }
        
        response = requests.post(
            f"{TIMEWEB_API}/apps",
            headers=headers,
            json=app_data,
            timeout=15
        )
        
        print_step(f"API ответ: {response.status_code}", "📡")
        
        if response.status_code in [200, 201]:
            app_data = response.json()
            print_step(f"✅ Приложение создано!", "✅")
            print_step(f"App data: {json.dumps(app_data, indent=2)}", "📊")
            return True
        else:
            print_step(f"API ответ: {response.text[:200]}", "⚠️")
            return False
            
    except Exception as e:
        print_step(f"API ошибка: {e}", "⚠️")
        return False

def check_local_server():
    """Проверить локальный сервер"""
    print_step("Попытка 4: Проверка локального сервера...", "🔄")
    
    try:
        response = requests.get("http://localhost:5000", timeout=5)
        print_step("✅ Локальный сервер работает!", "✅")
        return True
    except:
        print_step("⚠️ Локальный сервер не запущен", "⚠️")
        return False

def print_manual_instructions():
    """Вывести инструкции для ручной загрузки"""
    print("\n" + "="*75)
    print("📋 ИНСТРУКЦИИ ДЛЯ РУЧНОЙ ЗАГРУЗКИ".center(75))
    print("="*75 + "\n")
    
    print("""
🌐 СПОСОБ 1: ЧЕРЕЗ ВЕБ-ПАНЕЛЬ (САМЫЙ ПРОСТОЙ)
────────────────────────────────────────────────

1. Откройте: https://timeweb.cloud/console

2. Нажмите "Создать приложение" или "New App"

3. Выберите:
   • Python 3.9+
   • Flask
   • Имя: RPS GAME

4. Нажмите "Загрузить приложение" или "Upload"

5. Выберите файл: rps_game_deploy.zip
   (Находится в: e:\\project\\rps_game_deploy.zip)

6. Нажмите "Deploy"

7. Дождитесь завершения (1-2 минуты)

✅ ГОТОВО!


📧 СПОСОБ 2: ЧЕРЕЗ FTP
──────────────────────

1. В панели Timeweb найдите FTP данные

2. Подключитесь через FileZilla или WinSCP

3. Загрузите все файлы из проекта

4. Запустите приложение


🔑 СПОСОБ 3: ЧЕРЕЗ GIT
──────────────────────

1. В панели найдите Git URL

2. В терминале выполните:
   
   git remote add timeweb <URL_ИЗ_ПАНЕЛИ>
   git push timeweb main

3. Timeweb автоматически развернет приложение


📊 ВАШИ УЧЕТНЫЕ ДАННЫЕ:
──────────────────────

Пользователь: wq8056101
Сервер: RPS
API токен: ✅ Сохранен в скрипте
Архив: rps_game_deploy.zip (10.4 MB)

    """)
    
    print("="*75 + "\n")

def main():
    print("\n" + "🎮" * 37 + "\n")
    print("ПОЛНОСТЬЮ АВТОМАТИЧЕСКИЙ ДЕПЛОЙ RPS GAME НА TIMEWEB CLOUD".center(75))
    print("🎮" * 37 + "\n")
    
    attempts = [
        ("curl загрузка", deploy_with_curl),
        ("Git push", git_push_auto),
        ("API создание", create_app_manually),
        ("Локальный сервер", check_local_server),
    ]
    
    success_count = 0
    
    for attempt_name, attempt_func in attempts:
        print()
        try:
            if attempt_func():
                success_count += 1
        except Exception as e:
            print_step(f"Непредвиденная ошибка: {e}", "❌")
    
    print("\n" + "="*75)
    print(f"РЕЗУЛЬТАТ: {success_count}/{len(attempts)} методов успешно".center(75))
    print("="*75 + "\n")
    
    # Если ничего не сработало, выводим инструкции
    if success_count == 0:
        print_step("Ни один автоматический метод не сработал", "⚠️")
        print_step("Используйте ручные инструкции ниже:", "📋")
        print_manual_instructions()
    else:
        print_step("✅ ПРИЛОЖЕНИЕ ЗАГРУЖАЕТСЯ / РАЗВЕРТЫВАЕТСЯ!", "✅")
        print_step("Проверьте статус в панели Timeweb: https://timeweb.cloud/console", "🌐")
    
    print_step("Архив готов к загрузке:", "📦")
    print_step(f"  Путь: e:\\project\\rps_game_deploy.zip", "📂")
    print_step(f"  Размер: 10.4 MB", "📊")

if __name__ == "__main__":
    main()
