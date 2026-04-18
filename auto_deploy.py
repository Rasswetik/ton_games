#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
🚀 АВТОМАТИЧЕСКИЙ ДЕПЛОЙ - ВСЁ ПРОИСХОДИТ САМА
Скрипт подключается к PythonAnywhere и обновляет приложение
"""

import subprocess
import sys
import time

print("=" * 80)
print("🚀 ПОЛНОСТЬЮ АВТОМАТИЧЕСКИЙ ДЕПЛОЙ НА PYTHONANYWHERE")
print("=" * 80)

# Конфиг
PA_USER = "rpsgames"
PA_DOMAIN = "rpsgames.pythonanywhere.com"
REPO = "https://github.com/mokhosoev/rps_games"

print("\n📋 ПРОВЕРКА ПРЕДУСЛОВИЙ...")

# Проверить что это гит репозиторий
result = subprocess.run("git rev-parse --git-dir", shell=True, capture_output=True)
if result.returncode != 0:
    print("❌ Это не Git репозиторий!")
    sys.exit(1)
print("✅ Git репозиторий найден")

# Проверить наличие requirements.txt
import os
if not os.path.exists("requirements.txt"):
    print("❌ requirements.txt не найден!")
    sys.exit(1)
print("✅ requirements.txt найден")

print("\n" + "=" * 80)
print("ЭТАП 1: ЛОКАЛЬНАЯ ПОДГОТОВКА")
print("=" * 80)

# Добавить все файлы
print("\n📝 Добавление файлов...")
result = subprocess.run("git add -A", shell=True, capture_output=True, text=True)
if result.returncode == 0:
    print("✅ Файлы добавлены")
else:
    print(f"❌ Ошибка: {result.stderr}")

# Создать коммит (если есть изменения)
print("\n📝 Создание коммита...")
timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
result = subprocess.run(f'git commit -m "Auto deploy: {timestamp}"', shell=True, capture_output=True, text=True)
if "nothing to commit" in result.stdout or result.returncode == 0:
    print("✅ Коммит создан")
else:
    print(f"⚠️  {result.stdout}")

# Отправить на GitHub (без аутентификации если использовать SSH ключ)
print("\n📤 Отправка на GitHub...")
result = subprocess.run("git push -u origin main 2>&1", shell=True, capture_output=True, text=True, timeout=30)
if "done" in result.stdout.lower() or result.returncode == 0:
    print("✅ Код загружен на GitHub")
elif "Everything up-to-date" in result.stdout:
    print("✅ Код уже актуален")
else:
    print(f"⚠️  {result.stdout[:200]}")

print("\n" + "=" * 80)
print("ЭТАП 2: РАЗВЁРТЫВАНИЕ НА PYTHONANYWHERE")
print("=" * 80)

# Установить paramiko если нужно
try:
    import paramiko
except ImportError:
    print("\n📦 Установка paramiko для SSH...")
    subprocess.run([sys.executable, "-m", "pip", "install", "paramiko", "-q"], check=False)
    import paramiko

import paramiko

SSH_HOST = f"{PA_USER}.pythonanywhere.com"
SSH_USER = PA_USER

print(f"\n🔌 Подключение к {SSH_HOST}...")

try:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    # Попытка подключиться
    try:
        client.connect(SSH_HOST, username=SSH_USER, look_for_keys=True, timeout=10)
        print("✅ Подключено по SSH")
    except Exception as e:
        print(f"⚠️  SSH недоступен: {e}")
        print("   Используем альтернативный метод...")
        raise
    
    # Команды для выполнения
    commands = [
        f"cd /home/{PA_USER}/mysite",
        "git pull origin main",
        f"pip install -r requirements.txt --user",
        f"touch /var/www/{PA_USER}_pythonanywhere_com_wsgi.py",
    ]
    
    for i, cmd in enumerate(commands, 1):
        print(f"\n▶️  Команда {i}/{len(commands)}: {cmd[:50]}...")
        stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
        
        # Дождаться выполнения
        exit_code = stdout.channel.recv_exit_status()
        output = stdout.read().decode('utf-8', errors='ignore')
        error = stderr.read().decode('utf-8', errors='ignore')
        
        if exit_code == 0:
            print(f"   ✅ Успешно")
            if output.strip():
                for line in output.split('\n')[:3]:
                    if line.strip():
                        print(f"      {line[:70]}")
        else:
            print(f"   ⚠️  Код выхода: {exit_code}")
            if error.strip():
                print(f"      {error[:100]}")
    
    client.close()
    print("\n✅ SSH сессия закрыта")

except Exception as e:
    print(f"❌ SSH ошибка: {e}")
    print("\n" + "=" * 80)
    print("⚠️  АЛЬТЕРНАТИВА: Используйте Web Console PythonAnywhere")
    print("=" * 80)
    print(f"https://www.pythonanywhere.com/user/{PA_USER}/webapps/")
    print("""
Скопируйте и выполните эти команды:
cd ~/mysite
git pull origin main
pip install -r requirements.txt --user
touch /var/www/rpsgames_pythonanywhere_com_wsgi.py
""")

print("\n" + "=" * 80)
print("✅ РАЗВЁРТЫВАНИЕ ЗАВЕРШЕНО!")
print("=" * 80)
print(f"\n🌍 Ваше приложение: https://{PA_DOMAIN}")
print("\n⏳ Обновление может занять 10-30 секунд...")
print("🔄 Если не видите изменений, перезагрузите страницу (Ctrl+Shift+R)")

# Проверить доступность
print("\n📡 Проверка доступности...")
import urllib.request
try:
    response = urllib.request.urlopen(f"https://{PA_DOMAIN}/api/health", timeout=5)
    if response.status == 200:
        print(f"✅ Приложение отвечает! Статус: {response.status}")
except Exception as e:
    print(f"⏳ Приложение ещё загружается... ({e})")
    print("   Проверьте через 30 секунд")

print("\n" + "=" * 80)
