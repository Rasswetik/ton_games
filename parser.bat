@echo off
:: Устанавливаем кодировку UTF-8 для корректного отображения русского языка
chcp 65001 >nul
title TON Gifts Parser
color 0b

echo ========================================
echo   TON Gifts Parser - Запуск
echo ========================================

:: Проверка команды python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Команда 'python' не сработала, пробуем 'py'...
    goto use_py
) else (
    goto use_python
)

:use_python
echo [1/2] Проверка и установка библиотек (requests)...
python -m pip install requests
echo [2/2] Запуск скрипта парсера...
python parser.py
goto end

:use_py
py --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ОШИБКА] Python всё ещё не виден системе. 
    echo Убедитесь, что поставили галочку 'Add Python to PATH' при установке.
    pause
    exit
)
echo [1/2] Проверка и установка библиотек (requests)...
py -m pip install requests
echo [2/2] Запуск скрипта парсера...
py parser.py
goto end

:end
echo ========================================
echo   Работа завершена!
echo ========================================
pause