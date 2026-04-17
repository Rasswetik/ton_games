@echo off
chcp 65001 >nul

echo 1. Пробуем создать окружение...
py -m venv venv
if %errorlevel% neq 0 (echo Ошибка на этапе создания venv! && pause && exit)

echo 2. Активация и установка Flask...
:: Используем прямой путь к pip внутри venv, это надежнее
venv\Scripts\python.exe -m pip install flask

echo 3. Запуск приложения...
venv\Scripts\python.exe app.py

pause