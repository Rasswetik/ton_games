# 🎮 РПС GAMES

Приложение на Flask для игры РПС (Камень-Ножницы-Бумага) с интеграцией TON и промокодами.

## 🚀 Быстрый старт

### Локально (Windows)
```bash
# Установить зависимости и запустить
python run.py

# Приложение будет доступно на http://localhost:5000
```

### На сервере (PythonAnywhere)
```bash
# Развернуть на сервер
python deploy.py

# Приложение будет доступно на https://rpsgames.pythonanywhere.com
```

## 📁 Структура проекта

```
e:\project\
├── app.py                      # Основное Flask приложение
├── run.py                      # Запуск локально
├── deploy.py                   # Развертывание на сервер
├── requirements.txt            # Зависимости Python
├── wsgi.py                     # Конфиг для WSGI сервера
├── Procfile                    # Конфиг для деплоя
├── tonconnect-manifest.json    # Конфиг TON Connect
│
├── templates/                  # HTML шаблоны
│   ├── index.html             # Главная страница
│   ├── profile.html           # Профиль пользователя
│   ├── admin.html             # Админ панель
│   ├── market.html            # Маркетплейс
│   ├── crafts.html            # Крафт
│   └── bot.html               # Бот интеграция
│
├── static/                     # Статические файлы
│   ├── app.js                 # JavaScript логика
│   ├── style.css              # Стили
│   ├── data/
│   │   └── gifts.json         # Данные подарков
│   ├── img/gifts/             # Изображения подарков
│   └── gifs/                  # GIF анимации
│
├── data/                       # JSON хранилище
│   ├── users.json             # Данные пользователей
│   └── promos.json            # Данные промокодов
│
└── .git/                       # Git репозиторий
```

## 🔧 Конфигурация

### PythonAnywhere
- **Домен**: https://rpsgames.pythonanywhere.com
- **Username**: rpsgames
- **Token**: В коде deploy.py

### Telegram Bot
- **Token**: 8614240590:AAFcQVs8HvyY7jIo0noP_9dGNtS_zEkSMGI
- **Admin IDs**: 7679909245, 5257227556

### TON Connect
- **Manifest**: tonconnect-manifest.json

## 📦 Зависимости

- Flask 2.3.2
- Flask-SQLAlchemy 3.0.5
- Werkzeug 2.3.6
- requests 2.31.0
- python-dotenv 1.0.0

Установка: `pip install -r requirements.txt`

## 🎯 Основные функции

✅ Профиль пользователя с балансом TON  
✅ Активация промокодов с визуализацией награды  
✅ Инвентарь подарков  
✅ Админ панель  
✅ Маркетплейс  
✅ Система крафта  
✅ Интеграция с TON Connect  

## 🔐 API Endpoints

### Пользователь
- `POST /api/ton/init` - Инициализация пользователя
- `GET /api/user/get` - Получить данные пользователя
- `POST /api/user/update` - Обновить баланс/инвентарь

### Промокоды
- `GET /api/promo/activate/<code>/<user_id>` - Активировать промокод
- `GET /api/promo/list` - Список активных промокодов

### Админ
- `GET /api/admin/users` - Список пользователей
- `POST /api/admin/promo/create` - Создать промокод
- `POST /api/admin/user/edit` - Редактировать пользователя

### Здоровье
- `GET /api/health` - Проверка статуса приложения

## 💾 Хранилище данных

Все данные сохраняются в JSON файлах в папке `data/`:

### users.json
```json
{
  "7679909245": {
    "id": "7679909245",
    "balance": 100,
    "inventory": ["gift1", "gift2"],
    "is_new": false,
    "created_at": "2026-04-18T10:30:00"
  }
}
```

### promos.json
```json
{
  "SUMMER2024": {
    "name": "SUMMER2024",
    "type": "balance",
    "reward": 50,
    "max_activations": 100,
    "activations": 45,
    "used_by": ["7679909245", "5257227556"]
  }
}
```

## 🐛 Развертывание

### Локально
```bash
python run.py
```

### На PythonAnywhere
```bash
python deploy.py
```

Скрипт автоматически:
1. ✅ Проверит предусловия (Python, Git, файлы)
2. ✅ Отправит код на GitHub
3. ✅ Создаст архив
4. ✅ Загрузит на сервер (если SSH настроен)
5. ✅ Установит зависимости
6. ✅ Перезагрузит приложение
7. ✅ Проверит доступность

## 📝 Лицензия

Proprietary - 2026

## 👨‍💻 Разработчик

Created with ❤️ using Flask
