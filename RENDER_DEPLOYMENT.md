# 🚀 Render Deployment Instructions

Deploy RPS Games to Render.com (free tier) in 5 minutes.

## ✅ Requirements

- GitHub account with this repo
- Render.com account (free)
- Telegram Bot Token (already configured)

## 📋 Step-by-Step Guide

### Step 1: Connect GitHub to Render

1. Go to https://render.com
2. Click **"New+"** → **"Web Service"**
3. Click **"Connect Repository"**
4. Select **"Rasswetik/ton_games"** (or your fork)
5. Click **"Connect"**

### Step 2: Configure Service

| Setting | Value |
|---------|-------|
| **Name** | `rps-games-api` |
| **Runtime** | Python 3.13 |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn --bind 0.0.0.0:$PORT wsgi:app --timeout 120 --workers 2` |
| **Plan** | Free |

### Step 3: Add Environment Variables

In the **Environment** section, add:

```
FLASK_ENV=production
USE_DB=true
PORT=3000
```

### Step 4: Deploy

Click **"Create Web Service"**

Render will automatically:
- ✅ Pull latest code from GitHub
- ✅ Install Python dependencies
- ✅ Start the Flask application
- ✅ Assign you a free domain: `https://rps-games-api.onrender.com`

---

## 🎮 After Deployment

### 1. Test API
```bash
# Get user
curl https://rps-games-api.onrender.com/api/user/get?user_id=123456789

# Create invoice
curl -X POST https://rps-games-api.onrender.com/api/create-stars-invoice \
  -H "Content-Type: application/json" \
  -d '{"user_id":"123456789","stars_amount":10}'
```

### 2. Update Telegram Bot

In Telegram Mini App config, update webhook/API URL:
```
https://rps-games-api.onrender.com
```

### 3. Run Bot Locally

Bot must run locally (not on Render):
```bash
python bot_run_local.py
```

### 4. Access Game

When deployed:
- **Web App**: Open in Telegram: `https://t.me/rpsgames_robot/game`
- **API**: `https://rps-games-api.onrender.com`
- **Bot**: `@rpsgames_robot` on Telegram

---

## 📊 Monitoring

### Check Deployment Status

1. Go to Render Dashboard: https://dashboard.render.com
2. Select **"rps-games-api"**
3. View real-time logs and metrics

### Common Issues

#### Deploy fails with "module not found"
- Check `requirements.txt` has all modules
- Ensure main module is `app.py`
- Check Python version is 3.13+

#### "Address already in use" error
- Render assigns PORT automatically
- Make sure start command uses `$PORT` variable
- Current command: `--bind 0.0.0.0:$PORT`

#### Database locked
- Render may restart service - SQLite handles this
- Data persists in `/tmp` during free plan
- For persistent DB, upgrade to paid plan and add PostgreSQL

#### Payment system not working
- Check Telegram API access from Render
- Render may have proxy restrictions
- See fallback invoice generation in `app.py`

---

## 🔄 Auto-Deploy on Push

Once connected, every push to `main` branch auto-deploys:

```bash
git push origin main
```

Render automatically:
1. Detects push
2. Builds new image
3. Runs tests (if present)
4. Deploys without downtime
5. Updates live URL

---

## 💾 Database Persistence

### SQLite on Free Plan
- Database stored in **ephemeral storage** (resets on deploy)
- Lost when service restarts (every 15 min idle)
- For persistent DB: upgrade to paid plan or use PostgreSQL

### Backup Strategy
- Export `app.db` daily
- Upload to GitHub (use git-lfs for large files)
- Restore from backup if needed

### Recommended: Add PostgreSQL

For production, add PostgreSQL:
1. In Render Dashboard → create PostgreSQL database
2. Update connection string in `app.py`
3. Migrate data with `db.py` functions
4. Restart web service

---

## 🔐 Environment Secrets

For sensitive data:

1. In Render Dashboard → Environment
2. Add variables (they won't show in logs):
   ```
   TELEGRAM_BOT_TOKEN=<your-token>
   DATABASE_URL=postgres://...
   SECRET_KEY=<random-string>
   ```

3. Update `app.py` to read:
   ```python
   import os
   TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
   ```

---

## 📈 Scaling Up

### Free Plan Limits
- ✅ 750 hours/month
- ✅ Shared CPU
- ✅ 0.5 GB RAM
- ✅ Ephemeral storage only
- ❌ No persistent DB
- ❌ 15 min auto-idle

### Pro Plan ($7/month)
- ✅ Dedicated CPU
- ✅ 1 GB RAM
- ✅ Persistent storage
- ✅ No auto-idle
- ✅ Better performance
- ✅ PostgreSQL support

### Upgrade: Dashboard → Settings → Plan

---

## 🚨 Troubleshooting

### Service won't start
1. Check **Logs** tab
2. Look for Python errors
3. Verify `wsgi.py` exists
4. Check `requirements.txt` syntax

### Payment creation fails
1. Check Telegram API access: `curl https://api.telegram.org/`
2. Verify Bot Token is valid
3. Check logs for proxy errors
4. Fallback mode should still work

### Bot commands not responding
1. Bot runs **locally**, not on Render
2. Start with: `python bot_run_local.py`
3. Check bot is connected to Telegram
4. Verify polling is active (should see logs)

### Database is empty after deploy
1. Free Render uses ephemeral storage
2. Data lost on restart or deploy
3. Use PostgreSQL for persistence
4. Or export/import data from backup

---

## ✨ Pro Tips

1. **Monitor free hours**: Render gives 750/month, enough for ~24/7 uptime
2. **Use cron jobs**: Schedule backups, cleanups with simple endpoints
3. **Enable email alerts**: Get notified of deploy failures
4. **Keep Procfile updated**: Auto-deploy reads from it
5. **Test locally first**: Run `python run.py` before pushing
6. **Use git tags**: Deploy specific versions with `git tag v1.0.0`

---

## 🎯 What's Deployed

✅ **Flask API** - Game logic, payments, user management  
✅ **Database** - SQLite (ephemeral) or PostgreSQL (persistent)  
✅ **Static Files** - Frontend HTML/CSS/JS  
✅ **Telegram Integration** - Mini App with payment  

❌ **Not Deployed** - Bot (runs locally only)  
❌ **Not Included** - Database backups (manual only)  

---

## 📞 Support

- **Render Status**: https://status.render.com
- **Render Docs**: https://render.com/docs
- **Telegram Bot API**: https://core.telegram.org/bots/api
- **GitHub Issues**: https://github.com/Rasswetik/ton_games/issues

---

**Last Updated**: April 28, 2026  
**Status**: Ready for Production ✅
