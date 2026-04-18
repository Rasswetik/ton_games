#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
🚀 ПОЛНЫЙ ДЕПЛОЙ НА PYTHONANYWHERE ЧЕРЕЗ GIT
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime

def run_cmd(cmd, desc=""):
    """Выполнить команду и показать результат"""
    print(f"\n🔧 {desc}")
    print(f"   $ {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            print(f"   ✅ OK")
            if result.stdout:
                for line in result.stdout.split('\n')[:5]:
                    if line.strip():
                        print(f"      {line}")
            return True
        else:
            print(f"   ❌ ОШИБКА: {result.returncode}")
            if result.stderr:
                print(f"      {result.stderr[:200]}")
            return False
    except subprocess.TimeoutExpired:
        print(f"   ⏱️  ТАЙМАУТ (>60 сек)")
        return False
    except Exception as e:
        print(f"   ❌ {e}")
        return False

print("=" * 70)
print("🚀 ПОЛНОЕ РАЗВЁРТЫВАНИЕ НА PYTHONANYWHERE")
print("=" * 70)

# Этап 1: Git операции
print("\n" + "=" * 70)
print("ЭТАП 1: GIT - Синхронизация кода")
print("=" * 70)

run_cmd("git add -A", "Добавление всех файлов")
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
run_cmd(f'git commit -m "Deploy {timestamp}"', "Создание коммита")
run_cmd("git push origin main", "Отправка на GitHub")

# Этап 2: Проверка файлов
print("\n" + "=" * 70)
print("ЭТАП 2: ПРОВЕРКА - Критические файлы")
print("=" * 70)

files_to_check = [
    "app.py",
    "requirements.txt",
    "wsgi.py",
    "templates/index.html",
    "templates/profile.html",
    "templates/admin.html",
    "static/style.css",
]

all_ok = True
for f in files_to_check:
    if Path(f).exists():
        size = Path(f).stat().st_size
        print(f"   ✅ {f} ({size} bytes)")
    else:
        print(f"   ❌ {f} - НЕ НАЙДЕН")
        all_ok = False

# Этап 3: SSH инструкция
print("\n" + "=" * 70)
print("ЭТАП 3: СЕРВЕР - Инструкции для PythonAnywhere")
print("=" * 70)

print("""
📝 ВЫПОЛНИТЕ ЭТИ КОМАНДЫ НА СЕРВЕРЕ (через SSH или Web Console):

1️⃣  Перейти в папку проекта:
   cd ~/mysite

2️⃣  Обновить код с GitHub:
   git pull origin main

3️⃣  Переустановить зависимости:
   pip install -r requirements.txt --user

4️⃣  Перезагрузить приложение:
   touch /var/www/rpsgames_pythonanywhere_com_wsgi.py

5️⃣  Проверить логи:
   tail -20 /var/log/rpsgames.pythonanywhere.com.error.log

🌍 После этого приложение будет доступно:
   https://rpsgames.pythonanywhere.com
""")

print("=" * 70)
if all_ok:
    print("✅ ВСЕ ФАЙЛЫ ГОТОВЫ К ЗАГРУЗКЕ")
    print("=" * 70)
    print("\n📌 БЫСТРЫЙ СПОСОБ:")
    print("   Откройте Web Console на PythonAnywhere и выполните:")
    print("   git pull origin main && touch /var/www/rpsgames_pythonanywhere_com_wsgi.py")
else:
    print("❌ НЕКОТОРЫЕ ФАЙЛЫ НЕ НАЙДЕНЫ")
    print("=" * 70)
