# 🎮 RPS GAMES - Telegram Mini App

Multiplayer Rock-Paper-Scissors game with Telegram Stars payment integration and bot functionality.

**Status**: ✅ Production Ready on Render  
**Game Mode**: Multiplayer + Bot + Crafting System  
**Payment**: Telegram Stars (XTR)  
**Bot**: Local Polling Mode (separate from web service)

---

## 🚀 Deployment

### Option 1: Automatic Render Deployment (Recommended)

1. **Fork/Clone this repository** to your GitHub account
2. **Create Render account** at https://render.com
3. **Create new Web Service** on Render:
   - Connect to your GitHub repo
   - Runtime: Python 3.13
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn --bind 0.0.0.0:$PORT wsgi:app --timeout 120 --workers 2`
   - Add environment variables:
     ```
     FLASK_ENV=production
     USE_DB=true
     PORT=3000
     ```

4. **Deploy** - Render will automatically rebuild on every push to `main` branch

### Option 2: Manual Configuration

```bash
# Clone repository
git clone https://github.com/Rasswetik/ton_games.git
cd ton_games

# Install dependencies
pip install -r requirements.txt

# Run with gunicorn (production)
gunicorn --bind 0.0.0.0:3000 wsgi:app --timeout 120 --workers 2

# Or run with Flask (development)
python run.py
```

---

## 🤖 Telegram Bot (Local Only)

The bot runs **locally** on your development machine, NOT on Render.

### Why?
- Render free tier doesn't support long-polling
- Bot uses polling (not webhooks) to update game state
- Separate local bot prevents conflicts with web API

### Setup Bot Locally

1. **Install dependencies**:
```bash
pip install python-telegram-bot==20.1
pip install requests
```

2. **Run the bot**:
```bash
python -c "
from bot_handler import start_bot_async
start_bot_async(
    token='8614240590:AAFcQVs8HvyY7jIo0noP_9dGNtS_zEkSMGI',
    get_user_data_func=None,
    save_users_func=None,
    user_data={},
    promos={}
)
"
```

Or use the helper script:
```bash
python bot_run_local.py
```

3. **Check bot is running**:
- Open Telegram
- Search for `@rpsgames_robot`
- Send `/start`
- You should see bot menu with commands

---

## 💳 Payment System

### Telegram Stars Payment Flow

1. **User clicks** "Пополнить баланс" button
2. **Frontend creates invoice** via `/api/create-stars-invoice`
3. **Backend calls** Telegram Bot API to generate payment link
4. **Frontend opens** `https://t.me/$<invoice_id>` in Telegram
5. **User completes** payment in Telegram
6. **Frontend polls** `/api/user/get` to detect balance increase
7. **Server updates** balance in SQLite database
8. **Frontend confirms** payment and shows success

### Production Considerations

- **Retry Logic**: 3 attempts with exponential backoff
- **Timeout Handling**: 5-second timeout per request
- **Fallback Mode**: Uses synthetic invoice links if Telegram API fails
- **Polling**: 60 seconds, 1-second intervals
- **Status Detection**: Monitors balance changes to confirm payment

---

## 📁 Project Structure

```
e:\project/
├── app.py                    # Flask application & API routes
├── wsgi.py                   # Production WSGI entry point
├── run.py                    # Development runner
├── bot_handler.py            # Telegram bot with polling
├── db.py                     # SQLite database functions
├── multiplayer_db.py         # Multiplayer game logic
├── requirements.txt          # Python dependencies
├── render.yaml               # Render deployment config
│
├── templates/
│   ├── index.html           # Main game page
│   ├── game.html            # Game board
│   ├── multiplayer.html     # Multiplayer mode
│   ├── market.html          # In-app market
│   ├── profile.html         # User profile
│   ├── admin.html           # Admin panel
│   └── ...
│
├── static/
│   ├── app.js               # Frontend game logic
│   ├── style.css            # Styling
│   ├── tonconnect.js        # TON wallet integration
│   └── img/, vendor/
│
└── data/
    ├── users.json           # User data (SQLite used in production)
    ├── promos.json          # Promo codes
    └── ...
```

---

## 🔧 Configuration

### Environment Variables

```
FLASK_ENV=production           # Flask mode
USE_DB=true                    # Use SQLite (recommended)
USE_JSON=false                 # Disable JSON storage
PORT=3000                      # Server port (auto-detected on Render)
TELEGRAM_BOT_TOKEN=...         # Bot token (in code as fallback)
```

### Database

- **Production**: SQLite (`app.db`)
- **Backup**: JSON files in `data/` directory
- Auto-created on first run

---

## 🎮 Game Features

### Rock-Paper-Scissors
- Single-player vs bot
- Multiplayer vs other players
- Real-time synchronization

### Crafting System
- Combine items to create new items
- Progressive skill unlocks
- Inventory management

### Economy
- User balance in TON
- Telegram Stars payment
- Transaction history
- Referral bonuses

### Bot Commands
- `/start` - Begin game
- `/play` - Open mini-app
- `/stats` - Show statistics
- `/help` - Display help
- `/referral` - Get referral link

---

## 📊 API Endpoints

### User
- `GET /api/user/get?user_id=<id>` - Get user data
- `POST /api/user/update` - Update user profile

### Payments
- `POST /api/create-stars-invoice` - Create payment link
- `POST /api/process-stars-payment` - Confirm payment
- `GET /api/stars/balance/<user_id>` - Check balance

### Game
- `GET /game` - Game page
- `POST /api/game/move` - Make game move
- `GET /api/game/result` - Get game result

### Multiplayer
- `POST /api/multiplayer/create-room` - Create game room
- `POST /api/multiplayer/join-room` - Join room
- `POST /api/multiplayer/make-move` - Make move
- `GET /api/multiplayer/status/<room_id>` - Get room status

---

## 🐛 Troubleshooting

### Payment not loading
- Check Telegram API access (may be blocked by proxy on some hosts)
- Verify Bot Token is correct
- Check browser console for errors (F12)
- Try in different Telegram account/device

### Bot not responding
- Ensure bot is running locally with `python bot_run_local.py`
- Check logs for asyncio errors
- Verify `/start` command triggers in Telegram
- May need to restart if previous run crashed

### Database errors
- SQLite database locked: Check if multiple instances running
- Delete `app.db` to reset (will lose all user data)
- Falls back to JSON if SQLite fails

### Render deployment fails
- Check build logs in Render dashboard
- Verify `requirements.txt` has all dependencies
- Ensure `wsgi.py` exists and is correct
- Check free plan resource limits

---

## 🔐 Security

- ✅ Telegram user ID validation
- ✅ HTTPS only in production
- ✅ CSRF protection on forms
- ✅ Rate limiting on API endpoints
- ✅ SQLite database encrypted at rest (Render)
- ❌ Bot tokens stored in code (use env vars for production)

---

## 📈 Performance

- **Target**: Sub-second response times
- **Database**: SQLite (single file, fast for hobby apps)
- **Polling**: 1-second intervals for payment confirmation
- **Concurrency**: Gunicorn 2 workers on free Render plan

---

## 🤝 Contributing

1. Clone the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit changes (`git commit -am 'Add my feature'`)
4. Push to branch (`git push origin feature/my-feature`)
5. Open Pull Request

---

## 📄 License

Proprietary - RPS Games (2024-2026)

---

## 📞 Support

- **Bot**: @rpsgames_robot on Telegram
- **API**: Check `/api/help` endpoint
- **Issues**: Report via GitHub Issues
- **Feedback**: Send message to bot

---

## 🚀 Quick Links

- **Live Demo**: https://t.me/rpsgames_robot/game (when deployed)
- **GitHub**: https://github.com/Rasswetik/ton_games
- **Render Dashboard**: https://dashboard.render.com
- **Telegram Bot**: @rpsgames_robot

---

**Last Updated**: April 28, 2026  
**Status**: Production Ready ✅
