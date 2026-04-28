"""
Telegram Bot Handler - запускается вместе с Flask
"""
import logging
import threading
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Это будет заполнено из app.py
TELEGRAM_BOT_TOKEN = None
get_user_data_func = None
save_users_func = None
user_data_dict = None
promo_codes_dict = None

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start с поддержкой реферальных ссылок"""
    user = update.effective_user
    args = context.args
    
    referrer_id = None
    if args and len(args) > 0:
        # Проверить если это реферальная ссылка: /start ref_123456789
        arg = args[0]
        if arg.startswith('ref_'):
            referrer_id = arg.replace('ref_', '')
        # Или промокод: /start PROMO123
        elif promo_codes_dict and arg.upper() in promo_codes_dict:
            pass  # Обработаем промо ниже
    
    welcome_text = f"👋 Привет, {user.first_name}!\n\n"
    welcome_text += "🎮 Добро пожаловать в **RPS GAMES**!\n\n"
    welcome_text += "Здесь ты можешь:\n"
    welcome_text += "• 💰 Зарабатывать TON\n"
    welcome_text += "• 🎁 Собирать подарки\n"
    welcome_text += "• 🎯 Играть в мультиплеер\n"
    welcome_text += "• 🤝 Приглашать друзей\n\n"
    
    # Если это реферальная ссылка
    if referrer_id:
        welcome_text += f"✅ Ты присоединился через реферала!\n"
        welcome_text += f"Получи бонусы за приглашение!\n\n"
    
    # Получить или создать пользователя
    user_id = str(user.id)
    tg_full_name = user.first_name + (f" {user.last_name}" if user.last_name else "")
    
    if get_user_data_func and user_data_dict is not None:
        try:
            user_data = get_user_data_func(user_id, tg_id=user.id, referred_by=referrer_id, tg_name=tg_full_name)
            if user_data and user_data.get('is_new'):
                welcome_text += "🎁 **Добро пожаловать!** Тебе начислено 10 TON!\n"
                user_data['balance'] = 10
                user_data['is_new'] = False
                save_users_func(user_data_dict)
                logger.info(f"✅ New user {user_id} ({tg_full_name}) created with 10 TON bonus")
        except Exception as e:
            logger.error(f"❌ Error creating user {user_id}: {e}")
    
    keyboard = [
        [InlineKeyboardButton("🎮 Открыть игру", url="https://rpsgames.pythonanywhere.com")],
        [InlineKeyboardButton("🤝 Пригласить друзей", callback_data="referral")],
        [InlineKeyboardButton("❓ Помощь", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

async def referral_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /referral - получить реферальную ссылку"""
    user_id = str(update.effective_user.id)
    referral_link = f"https://t.me/rps_game_bot?start=ref_{user_id}"
    
    text = f"🤝 **Твоя реферальная ссылка:**\n\n"
    text += f"`{referral_link}`\n\n"
    text += "📊 За каждого приглашённого друга получай:\n"
    text += "• 10% от его покупок\n"
    text += "• 5 бонус-TON\n\n"
    text += "🔗 Поделись ссылкой в Telegram!"
    
    keyboard = [[InlineKeyboardButton("📋 Копировать", callback_data="copy_ref")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    text = "❓ **Справка**\n\n"
    text += "/start - Начать\n"
    text += "/referral - Реферальная ссылка\n"
    text += "/stats - Твоя статистика\n"
    text += "/play - Открыть игру\n\n"
    text += "🎮 [Открыть игру](https://rpsgames.pythonanywhere.com)"
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /stats - статистика пользователя"""
    user_id = str(update.effective_user.id)
    
    if get_user_data_func and user_data_dict is not None:
        user_data = get_user_data_func(user_id)
        
        text = f"📊 **Твоя статистика**\n\n"
        text += f"💰 Баланс: `{user_data['balance']:.2f} TON`\n"
        text += f"🎁 Подарков: `{len(user_data['inventory'])}`\n"
        text += f"🤝 Рефералов: `{len(user_data.get('referrals', []))}`\n"
        text += f"💵 Доход от рефералов: `{user_data.get('referral_earnings', 0):.2f} TON`\n"
        text += f"📅 Зарегистрирован: `{user_data['created_at'][:10]}`\n"
        
        await update.message.reply_text(text, parse_mode='Markdown')
    else:
        await update.message.reply_text("❌ Ошибка загрузки данных")

async def play_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /play - открыть игру"""
    keyboard = [[InlineKeyboardButton("🎮 Играть", url="https://rpsgames.pythonanywhere.com")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🎮 Нажми кнопку ниже чтобы открыть игру!",
        reply_markup=reply_markup
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на кнопки"""
    query = update.callback_query
    data = query.data
    
    logger.info(f"[BOT] Button callback received: {data} from user {query.from_user.id}")
    
    # Подтвердить что кнопка нажата
    await query.answer()
    
    if data == "copy_ref":
        user_id = str(query.from_user.id)
        referral_link = f"https://t.me/rpsgames_robot?start=ref_{user_id}"
        text = f"🤝 **Твоя реферальная ссылка:**\n\n"
        text += f"`{referral_link}`\n\n"
        text += "📊 За каждого приглашённого друга получай:\n"
        text += "• 10% от его покупок\n"
        text += "• 5 бонус-TON\n\n"
        text += "✅ Ссылка скопирована в буфер обмена!"
        await query.edit_message_text(text, parse_mode='Markdown')
    else:
        logger.warning(f"[BOT] Unknown callback data: {data}")
        await query.answer("❌ Неизвестная команда", show_alert=True)

def start_bot_async(token, user_data_func, save_users_func, user_data, promos):
    """Запустить бота в background потоке"""
    try:
        if not token or token.startswith('8614240590'):
            logger.warning(f"⚠️  Bot token seems invalid or placeholder")
        
        logger.info(f"🔄 Starting bot with token: {token[:20]}...")
        bot_thread = threading.Thread(
            target=_run_bot,
            args=(token, user_data_func, save_users_func, user_data, promos),
            daemon=True
        )
        bot_thread.start()
        logger.info("✅ Bot thread started successfully in background")
    except Exception as e:
        logger.error(f"❌ Failed to start bot: {e}")
        import traceback
        traceback.print_exc()

def _run_bot(token, user_data_func, save_users_func_arg, user_data, promos):
    """Internal function to run the bot"""
    import asyncio
    
    global TELEGRAM_BOT_TOKEN, get_user_data_func, save_users_func, user_data_dict, promo_codes_dict
    
    TELEGRAM_BOT_TOKEN = token
    get_user_data_func = user_data_func
    save_users_func = save_users_func_arg
    user_data_dict = user_data
    promo_codes_dict = promos
    
    async def main():
        try:
            logger.info(f"🔌 Connecting to Telegram Bot API...")
            app = Application.builder().token(token).build()
            
            # Добавить обработчики команд
            app.add_handler(CommandHandler("start", start_command))
            app.add_handler(CommandHandler("referral", referral_command))
            app.add_handler(CommandHandler("help", help_command))
            app.add_handler(CommandHandler("stats", stats_command))
            app.add_handler(CommandHandler("play", play_command))
            
            # Обработчик нажатий на кнопки
            app.add_handler(CallbackQueryHandler(button_callback))
            
            logger.info("✅ Telegram Bot handlers registered!")
            logger.info("🚀 Bot starting polling...")
            
            # Запустить бота (polling)
            await app.run_polling(allowed_updates=Update.ALL_TYPES)
        except Exception as e:
            logger.error(f"❌ Bot error in main(): {e}")
            import traceback
            traceback.print_exc()
            raise
    
    try:
        logger.info("🎬 Bot asyncio loop starting...")
        # Use new_event_loop instead of asyncio.run to avoid event loop conflicts
        # This is important when running bot in a background thread with Flask
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(main())
        finally:
            loop.close()
    except Exception as e:
        logger.error(f"❌ AsyncIO error: {e}")
        import traceback
        traceback.print_exc()
        # Попробовать перезапустить
        logger.info("🔄 Attempting bot restart in 10 seconds...")
        import time
        time.sleep(10)
        logger.info("🔄 Restarting bot...")
        _run_bot(token, user_data_func, save_users_func_arg, user_data, promos)
