@echo off
chcp 65001 > nul
set /p repo_url="Введите URL вашего репозитория GitHub: "

echo [*] Инициализация Git...
git init

echo [*] Добавление файлов...
:: Создаем .gitignore, чтобы не заливать лишнее
echo venv/ > .gitignore
echo *.pyc >> .gitignore
echo __pycache__/ >> .gitignore
echo .env >> .gitignore

git add .

echo [*] Создание первого коммита...
git commit -m "Initial commit - TON Game Project"

echo [*] Настройка ветки и удаленного репозитория...
git branch -M main
git remote add origin %repo_url%

echo [*] Отправка файлов на GitHub...
git push -u origin main --force

echo --------------------------------------------------
echo [+] Готово! Проверь свой репозиторий на сайте.
pause