#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
🚀 РПС GAMES - Скрипт развертывания на PythonAnywhere
Использование: python deploy.py

Функции:
- Загрузка файлов на сервер
- Установка зависимостей
- Перезагрузка приложения
- Проверка доступности
"""

import os
import sys
import subprocess
import json
import time
from pathlib import Path
from datetime import datetime
import shutil

# ===== КОНФИГУРАЦИЯ =====
PYTHONANYWHERE_DOMAIN = "rpsgames.pythonanywhere.com"
PYTHONANYWHERE_USERNAME = "rpsgames"
PYTHONANYWHERE_TOKEN = "299a1d0450b8726e11d9e04f21a5c8bb04a54bb0"

# Файлы/папки для загрузки
DEPLOY_FILES = [
    "app.py",
    "requirements.txt",
    "wsgi.py",
    "Procfile",
    "tonconnect-manifest.json",
    "templates/",
    "static/",
    "data/",
]

# ===== ЦВЕТА И СИМВОЛЫ =====
COLORS = {
    "RESET": "\033[0m",
    "BOLD": "\033[1m",
    "GREEN": "\033[92m",
    "RED": "\033[91m",
    "YELLOW": "\033[93m",
    "BLUE": "\033[94m",
    "CYAN": "\033[96m",
}

def log(msg, level="INFO"):
    """Красивое логирование"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    if level == "SUCCESS":
        prefix = f"{COLORS['GREEN']}✅{COLORS['RESET']}"
    elif level == "ERROR":
        prefix = f"{COLORS['RED']}❌{COLORS['RESET']}"
    elif level == "WARNING":
        prefix = f"{COLORS['YELLOW']}⚠️ {COLORS['RESET']}"
    elif level == "INFO":
        prefix = f"{COLORS['CYAN']}ℹ️ {COLORS['RESET']}"
    elif level == "DEPLOY":
        prefix = f"{COLORS['BLUE']}🚀{COLORS['RESET']}"
    else:
        prefix = "  "
    
    print(f"{prefix} [{timestamp}] {msg}")

def run_command(cmd, show_output=False):
    """Выполнить команду и вернуть результат"""
    try:
        if show_output:
            result = subprocess.run(cmd, shell=True, text=True)
        else:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def check_prerequisites():
    """Проверить необходимые предусловия"""
    log("Проверка предусловий...", "INFO")
    
    # Проверить Python
    success, _, _ = run_command("python --version")
    if not success:
        log("Python не найден!", "ERROR")
        return False
    log("Python установлен", "SUCCESS")
    
    # Проверить Git
    success, _, _ = run_command("git --version")
    if not success:
        log("Git не найден!", "ERROR")
        log("Установите Git с https://git-scm.com", "WARNING")
        return False
    log("Git установлен", "SUCCESS")
    
    # Проверить необходимые файлы
    for file in DEPLOY_FILES:
        if not Path(file).exists():
            log(f"Файл не найден: {file}", "ERROR")
            return False
    log("Все необходимые файлы найдены", "SUCCESS")
    
    return True

def create_archive():
    """Создать архив для загрузки"""
    log("Создание архива...", "DEPLOY")
    
    archive_name = "rps_games_deploy"
    
    # Удалить старый архив
    for ext in [".zip", ".tar.gz"]:
        path = archive_name + ext
        if Path(path).exists():
            Path(path).unlink()
    
    try:
        shutil.make_archive(archive_name, "zip", ".")
        log(f"Архив создан: {archive_name}.zip", "SUCCESS")
        return True, archive_name + ".zip"
    except Exception as e:
        log(f"Ошибка создания архива: {e}", "ERROR")
        return False, None

def git_push():
    """Отправить изменения на GitHub"""
    log("Отправка кода на GitHub...", "DEPLOY")
    
    # Проверить что это гит репозиторий
    if not Path(".git").exists():
        log("Это не Git репозиторий!", "ERROR")
        return False
    
    # Проверить есть ли изменения
    success, stdout, _ = run_command("git status --short")
    if not success:
        log("Ошибка при проверке Git статуса", "ERROR")
        return False
    
    if not stdout.strip():
        log("Нет изменений для отправки", "WARNING")
        return True
    
    # Добавить и отправить
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    commands = [
        ("git add -A", "Добавление файлов"),
        (f"git commit -m 'Auto-deploy {timestamp}'", "Создание коммита"),
        ("git push origin main", "Отправка на GitHub"),
    ]
    
    for cmd, desc in commands:
        log(desc, "INFO")
        success, _, stderr = run_command(cmd)
        if not success and "nothing to commit" not in stderr:
            log(f"Ошибка: {stderr}", "ERROR")
            return False
    
    log("Код успешно отправлен на GitHub", "SUCCESS")
    return True

def upload_via_scp(archive_path):
    """Загрузить архив на сервер через SCP"""
    log("Загрузка файлов на PythonAnywhere...", "DEPLOY")
    
    remote_path = f"{PYTHONANYWHERE_USERNAME}@ssh.pythonanywhere.com:/home/{PYTHONANYWHERE_USERNAME}/"
    
    cmd = f'scp "{archive_path}" {remote_path}'
    
    success, stdout, stderr = run_command(cmd, show_output=True)
    
    if not success:
        log("Ошибка загрузки: " + stderr, "ERROR")
        return False
    
    log("Архив загружен на сервер", "SUCCESS")
    return True

def install_on_pythonanywhere():
    """Установить зависимости на PythonAnywhere"""
    log("Установка зависимостей на сервере...", "DEPLOY")
    
    cmd = f"""
    curl -X POST https://www.pythonanywhere.com/api/v0/user/{PYTHONANYWHERE_USERNAME}/consoles/ \\
    -H "Authorization: Token {PYTHONANYWHERE_TOKEN}" \\
    --data "executable=/usr/bin/python3.10&source=pip install -r requirements.txt"
    """
    
    success, stdout, stderr = run_command(cmd)
    
    if not success:
        log("⚠️  Ошибка установки (проверьте вручную)", "WARNING")
        return True  # Продолжаем несмотря на ошибку
    
    log("Зависимости установлены", "SUCCESS")
    return True

def reload_pythonanywhere():
    """Перезагрузить приложение на PythonAnywhere"""
    log("Перезагрузка приложения на сервере...", "DEPLOY")
    
    cmd = f"""
    curl -X POST \\
    -H "Authorization: Token {PYTHONANYWHERE_TOKEN}" \\
    https://www.pythonanywhere.com/api/v0/user/{PYTHONANYWHERE_USERNAME}/webapps/{PYTHONANYWHERE_DOMAIN}/reload/
    """
    
    success, stdout, stderr = run_command(cmd)
    
    if not success or "error" in stdout.lower():
        log("Ошибка при перезагрузке: " + str(stdout or stderr), "ERROR")
        return False
    
    log("Приложение перезагружено", "SUCCESS")
    time.sleep(2)
    return True

def verify_deployment():
    """Проверить что приложение работает"""
    log("Проверка доступности приложения...", "INFO")
    
    try:
        import requests
        
        for attempt in range(3):
            try:
                response = requests.get(
                    f"https://{PYTHONANYWHERE_DOMAIN}/api/health",
                    timeout=5
                )
                
                if response.status_code == 200:
                    log(f"✅ Приложение доступно!", "SUCCESS")
                    log(f"🌐 https://{PYTHONANYWHERE_DOMAIN}", "INFO")
                    return True
            except:
                if attempt < 2:
                    log(f"Попытка {attempt + 1}/3 (ожидание {2 ** attempt}сек)...", "WARNING")
                    time.sleep(2 ** attempt)
        
        log("Приложение недоступно (проверьте вручную)", "WARNING")
        return False
        
    except ImportError:
        log("requests не установлен, пропуск проверки", "WARNING")
        return True

def main():
    """Главная функция"""
    print("\n" + "="*70)
    print(f"{COLORS['BOLD']}{COLORS['BLUE']}🎮 РПС GAMES - РАЗВЕРТЫВАНИЕ НА PYTHONANYWHERE{COLORS['RESET']}")
    print("="*70 + "\n")
    
    # 1. Проверка предусловий
    if not check_prerequisites():
        log("Критические ошибки при проверке!", "ERROR")
        sys.exit(1)
    
    print("\n" + "-"*70)
    print(f"{COLORS['BOLD']}ЭТАПЫ РАЗВЕРТЫВАНИЯ:{COLORS['RESET']}")
    print("-"*70)
    print("1️⃣  Git push на GitHub")
    print("2️⃣  Создание архива")
    print("3️⃣  Загрузка на сервер")
    print("4️⃣  Установка зависимостей")
    print("5️⃣  Перезагрузка приложения")
    print("6️⃣  Проверка доступности")
    print("-"*70 + "\n")
    
    # 2. Git push
    print(f"\n{COLORS['BOLD']}ЭТАП 1/6: Git Push{COLORS['RESET']}")
    print("-" * 70)
    if not git_push():
        log("Ошибка Git push (пропуск)", "WARNING")
    
    # 3. Создание архива
    print(f"\n{COLORS['BOLD']}ЭТАП 2/6: Создание архива{COLORS['RESET']}")
    print("-" * 70)
    success, archive_path = create_archive()
    if not success:
        log("Ошибка создания архива!", "ERROR")
        sys.exit(1)
    
    # 4. Загрузка
    print(f"\n{COLORS['BOLD']}ЭТАП 3/6: Загрузка на сервер{COLORS['RESET']}")
    print("-" * 70)
    if not upload_via_scp(archive_path):
        log("Ошибка загрузки (возможно SSH не настроена)", "WARNING")
    
    # 5. Установка зависимостей
    print(f"\n{COLORS['BOLD']}ЭТАП 4/6: Установка зависимостей{COLORS['RESET']}")
    print("-" * 70)
    install_on_pythonanywhere()
    
    # 6. Перезагрузка
    print(f"\n{COLORS['BOLD']}ЭТАП 5/6: Перезагрузка приложения{COLORS['RESET']}")
    print("-" * 70)
    if not reload_pythonanywhere():
        log("⚠️  Проверьте статус вручную", "WARNING")
    
    # 7. Проверка
    print(f"\n{COLORS['BOLD']}ЭТАП 6/6: Проверка доступности{COLORS['RESET']}")
    print("-" * 70)
    verify_deployment()
    
    # Итоговая информация
    print("\n" + "="*70)
    print(f"{COLORS['BOLD']}{COLORS['GREEN']}🎉 РАЗВЕРТЫВАНИЕ ЗАВЕРШЕНО{COLORS['RESET']}")
    print("="*70)
    print(f"\n📍 Приложение: {COLORS['CYAN']}https://{PYTHONANYWHERE_DOMAIN}{COLORS['RESET']}")
    print(f"📍 Профиль: {COLORS['CYAN']}https://{PYTHONANYWHERE_DOMAIN}/profile{COLORS['RESET']}")
    print(f"📍 API Health: {COLORS['CYAN']}https://{PYTHONANYWHERE_DOMAIN}/api/health{COLORS['RESET']}")
    print("\n" + "="*70 + "\n")
    
    # Очистка
    if Path(archive_path).exists():
        Path(archive_path).unlink()
        log(f"Архив удален: {archive_path}", "INFO")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{COLORS['YELLOW']}🛑 Развертывание отменено пользователем{COLORS['RESET']}\n")
        sys.exit(0)
    except Exception as e:
        log(f"Критическая ошибка: {e}", "ERROR")
        sys.exit(1)
