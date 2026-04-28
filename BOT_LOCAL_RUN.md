# 🤖 Локальный запуск бота

Этот файл описывает как запустить Telegram бота локально, а сайт на production сервере.

## 🎯 Зачем?

- **Локальный бот** - можно тестировать команды, обновлять функционал, видеть логи
- **Production сайт** - работает на основном сервере и обрабатывает платежи
- **Отдельные процессы** - не конфликтуют друг с другом

## 📋 Требования

- Python 3.13+
- Telegram Bot Token: `8614240590:AAFcQVs8HvyY7jIo0noP_9dGNtS_zEkSMGI`
- Интернет для подключения к Telegram API

## 🚀 Шаг 1: Установить зависимости бота

```bash
# На локальной машине
pip install python-telegram-bot==20.1
pip install requests
```

## 🚀 Шаг 2: Запустить бота локально

```bash
# На локальной машине
cd e:\project
python -c "
from bot_handler import start_bot_async
from datetime import datetime

# Запустить бота в blocking режиме
start_bot_async(
    token='8614240590:AAFcQVs8HvyY7jIo0noP_9dGNtS_zEkSMGI',
    get_user_data_func=None,
    save_users_func=None,
    user_data={},
    promos={}
)
"
```

Или запустить через отдельный скрипт:

```bash
python bot_run_local.py
```

## 🚀 Шаг 3: Запустить сайт на production (как обычно)

На production сервере:
```bash
cd /home/rpsgames/rps_game
python run.py
```

## ✅ Проверка

1. **Бот локально**: Откройте Telegram и напишите `/start` боту `@rpsgames_robot`
   - Должны появиться кнопки и меню
   - Логи должны быть в терминале

2. **Сайт на production**: 
   - Откройте браузер на `https://t.me/rpsgames_robot/game` или веб-адресс
   - Платежи должны работать через production Telegram API
   - Логи на production сервере

## 🔧 Логирование

### Бот (локально)
```
INFO:bot_handler:🎬 Bot asyncio loop starting...
INFO:bot_handler:✅ Telegram Bot handlers registered!
INFO:bot_handler:🚀 Bot starting polling...
```

### Платежи (production)
```
[STARS] ========== CREATE INVOICE START ==========
[STARS] Attempt 1/3 to call Telegram API...
[STARS] ✅ SUCCESS! Invoice link: https://t.me/$...
```

## ⚙️ Переменные окружения

- `TELEGRAM_BOT_TOKEN` - токен бота (в app.py, строка 2074)
- `USE_DB` - использовать SQLite (по умолчанию true)
- `USE_JSON` - использовать JSON файлы (по умолчанию false)

## 📱 Функции бота

- `/start` - начать игру
- `/play` - открыть мини-приложение
- `/stats` - показать статистику
- `/help` - справка
- `/referral` - реферальная ссылка

## 🐛 Решение проблем

### Бот не подключается к Telegram API

```
❌ AsyncIO error: Cannot close a running event loop
```

**Решение**: Используется `asyncio.new_event_loop()` вместо `asyncio.run()` для Flask совместимости.

### Платежи не работают

1. Проверьте что Bot Token правильный
2. Проверьте что бот **не запущен** на production сервере (чтобы не было конфликта)
3. Проверьте что платежи идут через production Telegram API

### Бот зависает

1. Нажмите Ctrl+C чтобы остановить
2. Проверьте логи на предмет ошибок asyncio
3. Перезагрузите процесс

## 📊 Архитектура

```
┌─────────────────────────────────────────────────────┐
│              Telegram (@rpsgames_robot)             │
├─────────────────────────────────────────────────────┤
│                                                       │
│  ┌────────────────┐         ┌────────────────────┐  │
│  │  Бот локально  │         │ Сайт на production │  │
│  │                │         │                    │  │
│  │ Polling Mode   │         │ Flask API          │  │
│  │ /start, /play  │         │ Платежи, Игры      │  │
│  │                │         │                    │  │
│  └────────────────┘         └────────────────────┘  │
│        ↓                              ↓               │
│    Telegram                    Telegram Bot API      │
│    Bot Updates                 createInvoiceLink()   │
│                                                       │
└─────────────────────────────────────────────────────┘
```

## 📞 Контакты

- Bot Token: `8614240590:AAFcQVs8HvyY7jIo0noP_9dGNtS_zEkSMGI`
- Bot Username: `@rpsgames_robot`
- Production server: rpsgames.ru (или текущий хост)
