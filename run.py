#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Скрипт для установки зависимостей и запуска приложения Flask
Использование: python run.py
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def run_command(cmd, description=""):
    """Выполнить команду в терминале"""
    if description:
        print(f"\n{'='*60}")
        print(f"▶ {description}")
        print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=False, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Ошибка при выполнении: {e}")
        return False

def check_python():
    """Проверить версию Python"""
    print(f"🐍 Python версия: {sys.version}")
    if sys.version_info < (3, 7):
        print("❌ Требуется Python 3.7 или выше!")
        sys.exit(1)
    print("✅ Версия Python OK\n")

def install_requirements():
    """Установить зависимости из requirements.txt"""
    req_file = Path("requirements.txt")
    
    if not req_file.exists():
        print("⚠️  requirements.txt не найден!")
        return False
    
    print(f"📦 Файл зависимостей: {req_file}")
    
    # Определить команду для pip
    if platform.system() == "Windows":
        pip_cmd = f"{sys.executable} -m pip install -r requirements.txt"
    else:
        pip_cmd = f"python3 -m pip install -r requirements.txt"
    
    return run_command(pip_cmd, "Установка зависимостей")

def create_data_directory():
    """Создать папку data для JSON хранилища"""
    data_dir = Path("data")
    if not data_dir.exists():
        data_dir.mkdir(exist_ok=True)
        print(f"✅ Создана папка {data_dir}/")
    else:
        print(f"✅ Папка {data_dir}/ уже существует")

def run_app():
    """Запустить приложение Flask"""
    if platform.system() == "Windows":
        flask_cmd = f"{sys.executable} -m flask run --host=0.0.0.0 --port=5000"
    else:
        flask_cmd = "python3 -m flask run --host=0.0.0.0 --port=5000"
    
    print("\n" + "="*60)
    print("🚀 ЗАПУСК ПРИЛОЖЕНИЯ")
    print("="*60)
    print("📍 Адрес: http://localhost:5000")
    print("🛑 Для остановки нажмите Ctrl+C")
    print("="*60 + "\n")
    
    # Установить переменную окружения
    os.environ['FLASK_APP'] = 'app.py'
    os.environ['FLASK_ENV'] = 'development'
    
    run_command(flask_cmd, "")

def main():
    """Главная функция"""
    print("\n" + "="*60)
    print("🎮 РПС GAMES - АВТОЗАПУСК")
    print("="*60 + "\n")
    
    # 1. Проверка Python
    check_python()
    
    # 2. Создать data папку
    print("📁 Проверка папок...")
    create_data_directory()
    
    # 3. Установить зависимости
    print("\n📦 Проверка зависимостей...")
    if not install_requirements():
        print("⚠️  Ошибка при установке зависимостей, но продолжаем...")
    
    # 4. Запустить приложение
    run_app()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Приложение остановлено пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        sys.exit(1)
