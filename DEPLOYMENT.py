#!/usr/bin/env python3
"""
Инструкция по деплою RPS GAME на Timeweb Cloud через панель управления
"""

DEPLOYMENT_INSTRUCTIONS = """
╔════════════════════════════════════════════════════════════════╗
║               ДЕПЛОЙ RPS GAME НА TIMEWEB CLOUD                 ║
╚════════════════════════════════════════════════════════════════╝

✅ ВСЕ ФАЙЛЫ ГОТОВЫ К ЗАГРУЗКЕ

📋 ВАРИАНТ 1: ЧЕРЕЗ ПАНЕЛЬ TIMEWEB (Рекомендуется)
───────────────────────────────────────────────────

1. Откройте https://timeweb.cloud
2. Войдите в свой аккаунт (user: wq8056101)
3. Перейдите в раздел "Приложения" или "Облачные приложения"
4. Нажмите "Создать приложение" или "Новое приложение"
5. Выберите:
   - Язык: Python 3.9+
   - Фреймворк: Flask
   - Имя приложения: RPS GAME
   
6. После создания приложения:
   - Выберите способ развертывания: GIT
   - Нажмите "Генерировать токен" или используйте существующий
   
7. В терминале выполните:
   
   cd e:\\project
   git remote add timeweb <URL_РЕПОЗИТОРИЯ_ИЗ_ПАНЕЛИ>
   git push timeweb main
   
   (URL выглядит примерно так: https://git.timeweb.cloud/...)

8. Приложение автоматически развернется после push'а

───────────────────────────────────────────────────────────────

📋 ВАРИАНТ 2: ЧЕРЕЗ FTP (Альтернатива)
───────────────────────────────────────

1. В панели Timeweb найдите FTP-учетные данные приложения
2. Подключитесь через FTP-клиент (FileZilla, WinSCP)
3. Загрузите все файлы из проекта в корневую папку

───────────────────────────────────────────────────────────────

📋 ВАРИАНТ 3: ЧЕРЕЗ ЗАГРУЗКУ АРХИВА (Быстро)
──────────────────────────────────────────────

1. В папке проекта выполните:

   $folders = @('static', 'templates')
   $files = @('app.py', 'requirements.txt', 'Procfile', '.gitignore')
   
   Compress-Archive -Path $folders + $files -DestinationPath rps-game.zip

2. В панели Timeweb нажмите "Загрузить приложение"
3. Выберите файл rps-game.zip
4. Дождитесь развертывания

───────────────────────────────────────────────────────────────

🔧 КОНФИГУРАЦИЯ НА СЕРВЕРЕ
──────────────────────────

Убедитесь, что в панели Timeweb установлены переменные окружения:

PORT: 5000  (или автоматически определяемый порт)
DEBUG: False

───────────────────────────────────────────────────────────────

📊 ПРОВЕРКА СТАТУСА ПРИЛОЖЕНИЯ
───────────────────────────────

1. После развертывания перейдите на URL приложения
2. Проверьте логи в разделе "Логи приложения"
3. Если есть ошибки, исправьте requirements.txt и пересоберите

───────────────────────────────────────────────────────────────

✅ ГОТОВЫЕ ФАЙЛЫ В ПРОЕКТЕ
──────────────────────────

✓ app.py           - Основное приложение Flask
✓ requirements.txt - Зависимости Python
✓ Procfile         - Конфигурация для запуска
✓ templates/       - HTML шаблоны
✓ static/          - CSS, JS, изображения
✓ .gitignore       - Исключения Git

───────────────────────────────────────────────────────────────

🎮 ВАШ ТОКЕН API
────────────────

eyJhbGciOiJSUzUxMiIsInR5cCI6IkpXVCIsImtpZCI6IjFrYnhacFJNQGJSI0tSbE1xS1lqIn0.
eyJ1c2VyIjoid3E4MDU2MTAiLCJ0eXBlIjoiYXBpX2tleSIsImFwaV9rZXlfaWQiOiI2NjAxODda
Ny01NTEzLTQzN2ItOTE3Zi0xOTk1ZWFiOWUyYmYiLCJpYXQiOjE3NzY0Mjk0MTZ9.fTei_ZOn-Wfrn
ggGkyt5VWUkFp8SSf-Rcycs51jR8ar_AcUdjesxKOJfQSjiiWiNsB779knN_Gqu-Zupo4a0-I6rqj08d
OIYaT6o3wTyQA7-OqqdtfDrQKx1nGrAYXpkoY1jQEeisB9prvfboLO4UWrVQW_tb_Cp7Ix3C-wyLdGNK
gOMRlsOKFM6EdORAGXzNEZQxZqLuieWzdldJ_cZw3t7_TEg9b2AiEYVw_dPE3k6Vkq3Sn23Ugn5ejlQZ
vbvFrLwjSQgLFwYb12DcYFAfj9qozmO0xMtsmtROzx4Mz8qy3I4lTJBCkdo5EGWGtpUxg3gDTXv_DKrI
VKgIp3Kk5gAqFWUbdMD2px9Wh5SYK91SWEF0QleKfaXa7GCkjsOdi4zDZqx6V7GGtdti92Na3VQRwubUP
OgSeZ-yTP4nvNoaO-OxjdqJxB8wz9n9CMLQr9WfkUwSFzyzGuYPrR-IcVEPwHrwQ9yayurViC9nPxf56LN
FILbQ2PIe4X5zH7T

────────────────────────────────────────────────────────────────

Пользователь: wq8056101
Сервер: RPS

════════════════════════════════════════════════════════════════
"""

print(DEPLOYMENT_INSTRUCTIONS)

# Создаем пошаговую инструкцию в файл
with open("DEPLOYMENT.txt", "w", encoding="utf-8") as f:
    f.write(DEPLOYMENT_INSTRUCTIONS)

print("\n💾 Инструкция сохранена в файл: DEPLOYMENT.txt")
print("\n🚀 Проект готов к развертыванию!")
print("📍 Перейдите на https://timeweb.cloud и следуйте инструкциям выше")
