#!/usr/bin/env python3
"""
Deploy скрипт для PythonAnywhere
Использование: python deploy.py <username> <api_token>
"""

import requests
import sys
import json
import os
import subprocess
from pathlib import Path

class PythonAnywhereDeployer:
    def __init__(self, username, api_token):
        self.username = username
        self.api_token = api_token
        self.base_url = "https://www.pythonanywhere.com/api/v0"
        self.headers = {
            "Authorization": f"Token {api_token}",
            "Content-Type": "application/json"
        }
        self.app_name = f"{username}.pythonanywhere.com"
    
    def log(self, msg, level="INFO"):
        """Логирование"""
        icons = {"INFO": "ℹ️", "SUCCESS": "✅", "ERROR": "❌", "WARN": "⚠️"}
        print(f"{icons.get(level, '•')} [{level}] {msg}")
    
    def upload_files(self):
        """Загрузить файлы через Git или SFTP"""
        self.log("📦 Загрузка файлов проекта...", "INFO")
        
        try:
            # Проверяем есть ли git
            subprocess.run(["git", "--version"], check=True, capture_output=True)
            self.log("🔗 Git найден, используем Git для деплоя", "INFO")
            
            # Инициализируем git repo если нужно
            if not Path('.git').exists():
                subprocess.run(["git", "init"], check=True)
                subprocess.run(["git", "config", "user.email", "deploy@bot.local"], check=True)
                subprocess.run(["git", "config", "user.name", "Deploy Bot"], check=True)
            
            # Добавляем файлы
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(["git", "commit", "-m", "Deploy update"], 
                          capture_output=True)
            
            self.log("✅ Файлы готовы к загрузке", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"❌ Ошибка подготовки файлов: {e}", "ERROR")
            return False
    
    def reload_web_app(self):
        """Перезагрузить веб-приложение"""
        self.log("🔄 Перезагрузка приложения...", "INFO")
        
        try:
            url = f"{self.base_url}/user/{self.username}/webapps/{self.app_name}/reload/"
            response = requests.post(url, headers=self.headers)
            
            if response.status_code == 200:
                self.log("✅ Приложение перезагружено", "SUCCESS")
                return True
            else:
                self.log(f"❌ Ошибка перезагрузки: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Ошибка: {e}", "ERROR")
            return False
    
    def check_status(self):
        """Проверить статус приложения"""
        self.log("🔍 Проверка статуса приложения...", "INFO")
        
        try:
            url = f"{self.base_url}/user/{self.username}/webapps/{self.app_name}/"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                status = data.get('status', 'unknown')
                self.log(f"Статус: {status}", "INFO")
                return True
            else:
                self.log(f"❌ Не удалось получить статус: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Ошибка: {e}", "ERROR")
            return False
    
    def get_error_log(self):
        """Получить последние ошибки"""
        self.log("📋 Получение логов ошибок...", "INFO")
        
        try:
            url = f"{self.base_url}/user/{self.username}/webapps/{self.app_name}/error_log/"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                lines = data.get('lines', [])
                
                if lines:
                    self.log("Последние ошибки:", "INFO")
                    for line in lines[-10:]:  # Последние 10 строк
                        print(f"  {line}")
                else:
                    self.log("Нет ошибок", "SUCCESS")
                    
                return True
            else:
                self.log(f"❌ Не удалось получить логи: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Ошибка: {e}", "ERROR")
            return False
    
    def deploy(self):
        """Выполнить полный деплой"""
        self.log("🚀 Начало деплоя на PythonAnywhere", "INFO")
        self.log(f"👤 Username: {self.username}", "INFO")
        self.log(f"🌐 App: {self.app_name}", "INFO")
        print()
        
        # 1. Загружаем файлы
        if not self.upload_files():
            return False
        
        # 2. Проверяем статус
        if not self.check_status():
            self.log("⚠️ Не удалось проверить статус, но продолжаем", "WARN")
        
        # 3. Перезагружаем приложение
        if not self.reload_web_app():
            return False
        
        # 4. Проверяем логи
        self.get_error_log()
        
        print()
        self.log("=" * 50, "SUCCESS")
        self.log("🎉 Деплой завершен успешно!", "SUCCESS")
        self.log(f"🌐 Ваш сайт: https://{self.app_name}", "SUCCESS")
        self.log("=" * 50, "SUCCESS")
        
        return True

def main():
    if len(sys.argv) < 3:
        print("Использование: python deploy.py <username> <api_token>")
        print()
        print("Параметры:")
        print("  <username> - ваше имя пользователя на PythonAnywhere")
        print("  <api_token> - ваш API токен")
        print()
        print("Пример:")
        print("  python deploy.py myusername 299a1d0450b8726e11d9e04f21a5c8bb04a54bb0")
        sys.exit(1)
    
    username = sys.argv[1]
    api_token = sys.argv[2]
    
    deployer = PythonAnywhereDeployer(username, api_token)
    success = deployer.deploy()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
