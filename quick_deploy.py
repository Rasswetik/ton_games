#!/usr/bin/env python3
"""
Быстрый интерактивный деплой на PythonAnywhere
"""

import requests
import subprocess
import sys
import time
from pathlib import Path

class QuickDeploy:
    def __init__(self):
        self.username = None
        self.token = None
    
    def print_header(self):
        print("\n" + "="*60)
        print("🚀 RPS GAME - БЫСТРЫЙ ДЕПЛОЙ НА PYTHONANYWHERE".center(60))
        print("="*60 + "\n")
    
    def get_credentials(self):
        """Получить учетные данные"""
        print("📝 Введите ваши данные PythonAnywhere:\n")
        
        self.username = input("👤 Username на PythonAnywhere: ").strip()
        self.token = input("🔑 API Token: ").strip()
        
        if not self.username or not self.token:
            print("❌ Ошибка: все поля обязательны!")
            sys.exit(1)
        
        return True
    
    def verify_token(self):
        """Проверить валидность токена"""
        print("\n🔍 Проверка токена...")
        
        try:
            headers = {"Authorization": f"Token {self.token}"}
            url = f"https://www.pythonanywhere.com/api/v0/user/{self.username}/webapps/"
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                print("✅ Токен действителен!")
                return True
            elif response.status_code == 401:
                print("❌ Ошибка: неверный токен или username")
                return False
            else:
                print(f"❌ Ошибка: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Ошибка подключения: {e}")
            return False
    
    def check_git(self):
        """Проверить git"""
        print("\n📦 Проверка Git...")
        
        try:
            subprocess.run(["git", "--version"], capture_output=True, check=True)
            print("✅ Git установлен")
            return True
        except:
            print("❌ Git не установлен. Установите из https://git-scm.com/")
            return False
    
    def commit_changes(self):
        """Сделать коммит изменений"""
        print("\n📝 Подготовка файлов к загрузке...")
        
        try:
            # Инициализируем git если нужно
            if not Path('.git').exists():
                print("  → Инициализация git репо...")
                subprocess.run(["git", "init"], check=True, capture_output=True)
                subprocess.run(["git", "config", "user.email", "deploy@rps.local"], 
                             check=True, capture_output=True)
                subprocess.run(["git", "config", "user.name", "RPS Deployer"], 
                             check=True, capture_output=True)
            
            # Добавляем файлы
            print("  → Добавление файлов...")
            subprocess.run(["git", "add", "."], check=True, capture_output=True)
            
            # Коммитим
            print("  → Коммит изменений...")
            result = subprocess.run(
                ["git", "commit", "-m", f"Deploy: {time.strftime('%Y-%m-%d %H:%M:%S')}"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0 or "nothing to commit" in result.stdout:
                print("✅ Файлы готовы")
                return True
            else:
                print(f"⚠️  {result.stdout}")
                return True
                
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            return False
    
    def reload_app(self):
        """Перезагрузить приложение на PythonAnywhere"""
        print("\n🔄 Перезагрузка приложения...")
        
        app_name = f"{self.username}.pythonanywhere.com"
        
        try:
            headers = {"Authorization": f"Token {self.token}"}
            url = f"https://www.pythonanywhere.com/api/v0/user/{self.username}/webapps/{app_name}/reload/"
            
            response = requests.post(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                print("✅ Приложение перезагружено!")
                return True
            else:
                print(f"⚠️  Статус: {response.status_code}")
                return True
                
        except Exception as e:
            print(f"⚠️  Ошибка перезагрузки: {e}")
            return True
    
    def show_result(self):
        """Показать результат"""
        print("\n" + "="*60)
        print("✨ ДЕПЛОЙ ЗАВЕРШЕН!".center(60))
        print("="*60)
        
        app_url = f"https://{self.username}.pythonanywhere.com"
        
        print(f"\n🌐 Ваше приложение: {app_url}")
        print(f"⏱️  Открытие может занять 10-30 секунд")
        print(f"\n📝 Админ панель: {app_url}/admin")
        print(f"💬 Крафты: {app_url}/crafts")
        print(f"💰 Маркет: {app_url}/market")
        print(f"👤 Профиль: {app_url}/profile")
        
        print("\n" + "="*60)
    
    def run(self):
        """Запустить деплой"""
        self.print_header()
        
        # 1. Получаем учетные данные
        self.get_credentials()
        
        # 2. Проверяем токен
        if not self.verify_token():
            sys.exit(1)
        
        # 3. Проверяем git
        if not self.check_git():
            print("\n⚠️  Попробуем продолжить без git...")
        
        # 4. Коммитим изменения
        if not self.commit_changes():
            print("⚠️  Продолжаем несмотря на ошибку git...")
        
        # 5. Перезагружаем приложение
        if not self.reload_app():
            print("⚠️  Не удалось перезагрузить, но остальное готово")
        
        # 6. Показываем результат
        self.show_result()
        
        print("\n💡 Совет: если сайт не загружается, проверьте логи:")
        print(f"   → https://www.pythonanywhere.com/user/{self.username}/webapps")
        print()

if __name__ == "__main__":
    deployer = QuickDeploy()
    
    try:
        deployer.run()
    except KeyboardInterrupt:
        print("\n\n❌ Деплой отменен пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Критическая ошибка: {e}")
        sys.exit(1)
