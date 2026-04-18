@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM ===== RPS GAME DEPLOY SCRIPT =====
REM Автоматический деплой на PythonAnywhere

echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║                                                                ║
echo ║     🚀 RPS GAME - DEPLOY НА PYTHONANYWHERE                    ║
echo ║                                                                ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.

REM Проверяем Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не установлен или не в PATH
    echo 📥 Скачайте Python с https://python.org
    pause
    exit /b 1
)

echo ✅ Python найден
echo.

REM Проверяем requirements
echo 📦 Проверка зависимостей...
python -m pip install requests --quiet >nul 2>&1

if errorlevel 1 (
    echo ❌ Ошибка установки зависимостей
    pause
    exit /b 1
)

echo ✅ Зависимости готовы
echo.

REM Запускаем deploy
echo 🚀 Запуск деплоя...
echo.

python deploy_final.py
if errorlevel 1 (
    echo.
    echo ❌ Деплой завершился с ошибкой
    pause
    exit /b 1
) else (
    echo.
    echo ✅ Деплой успешно завершен!
    echo.
    echo 🌐 Откройте в браузере: https://rpsgames.pythonanywhere.com
    echo.
    pause
)
