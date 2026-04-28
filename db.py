"""
SQLite Database Module
Управление всеми данными приложения в SQLite
"""

import sqlite3
from pathlib import Path
from datetime import datetime
import json
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('DB')

DB_PATH = Path('app.db')

# Глобальное соединение
_connection = None

def get_connection():
    """Получить подключение к БД"""
    global _connection
    if _connection is None:
        _connection = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        _connection.row_factory = sqlite3.Row
    return _connection

def init_db():
    """Инициализировать БД и создать таблицы"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Таблица пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            tg_id INTEGER,
            tg_name TEXT,
            balance REAL DEFAULT 0,
            stars_balance REAL DEFAULT 0,
            is_new BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            referred_by TEXT,
            referral_earnings REAL DEFAULT 0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (referred_by) REFERENCES users(user_id)
        )
    ''')
    
    # Таблица инвентаря
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            gift_id INTEGER NOT NULL,
            gift_name TEXT,
            quantity INTEGER DEFAULT 1,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            UNIQUE(user_id, gift_id)
        )
    ''')
    
    # Таблица промокодов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS promo_codes (
            code TEXT PRIMARY KEY,
            reward_ton REAL DEFAULT 0,
            reward_stars REAL DEFAULT 0,
            uses_limit INTEGER DEFAULT 1,
            uses_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
    ''')
    
    # Таблица использованных промокодов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS used_promos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            code TEXT NOT NULL,
            used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (code) REFERENCES promo_codes(code),
            UNIQUE(user_id, code)
        )
    ''')
    
    # Таблица заявок на вывод
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS withdrawals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            amount REAL NOT NULL,
            currency TEXT DEFAULT 'TON',
            status TEXT DEFAULT 'pending',
            ton_tx_hash TEXT,
            stars_tx_hash TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')
    
    # Таблица пополнений
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS topups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            amount REAL NOT NULL,
            currency TEXT NOT NULL,
            ton_tx_hash TEXT,
            stars_tx_hash TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')
    
    # Таблица истории транзакций
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            type TEXT NOT NULL,
            amount REAL NOT NULL,
            currency TEXT DEFAULT 'TON',
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')
    
    # Таблица рефералов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            referrer_id TEXT NOT NULL,
            referral_id TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            earnings REAL DEFAULT 0,
            FOREIGN KEY (referrer_id) REFERENCES users(user_id),
            FOREIGN KEY (referral_id) REFERENCES users(user_id),
            UNIQUE(referrer_id, referral_id)
        )
    ''')
    
    # Таблица рынка (покупка/продажа подарков)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS market_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            gift_id INTEGER,
            gift_name TEXT,
            action TEXT NOT NULL,
            quantity INTEGER,
            price_per_unit REAL,
            total_price REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')
    
    conn.commit()
    logger.info("[DB] Database initialized successfully")

# ===== ФУНКЦИИ ПОЛЬЗОВАТЕЛЕЙ =====

def get_user(user_id):
    """Получить пользователя по ID"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (str(user_id),))
    row = cursor.fetchone()
    if row:
        return dict(row)
    return None

def create_or_get_user(user_id, tg_id=None, tg_name=None, referred_by=None):
    """Создать или получить пользователя"""
    conn = get_connection()
    cursor = conn.cursor()
    
    user_id_str = str(user_id)
    user = get_user(user_id_str)
    
    if user:
        return user
    
    cursor.execute('''
        INSERT INTO users (user_id, tg_id, tg_name, referred_by)
        VALUES (?, ?, ?, ?)
    ''', (user_id_str, tg_id, tg_name or 'User', referred_by))
    
    conn.commit()
    logger.info(f"[DB] Created user {user_id_str}")
    
    # Если есть реферер, добавить в таблицу рефералов
    if referred_by:
        cursor.execute('''
            INSERT OR IGNORE INTO referrals (referrer_id, referral_id)
            VALUES (?, ?)
        ''', (str(referred_by), user_id_str))
        conn.commit()
    
    return get_user(user_id_str)

def update_user_balance(user_id, amount, currency='TON'):
    """Обновить баланс пользователя"""
    conn = get_connection()
    cursor = conn.cursor()
    
    user_id_str = str(user_id)
    
    if currency == 'TON':
        cursor.execute('''
            UPDATE users 
            SET balance = balance + ?, last_updated = CURRENT_TIMESTAMP
            WHERE user_id = ?
        ''', (amount, user_id_str))
    elif currency == 'STARS':
        cursor.execute('''
            UPDATE users 
            SET stars_balance = stars_balance + ?, last_updated = CURRENT_TIMESTAMP
            WHERE user_id = ?
        ''', (amount, user_id_str))
    
    conn.commit()
    
    # Добавить в историю
    add_transaction(user_id_str, 'balance_update', amount, currency)
    
    return get_user(user_id_str)

def get_user_balance(user_id):
    """Получить баланс пользователя"""
    user = get_user(str(user_id))
    if user:
        return {
            'ton': user['balance'],
            'stars': user['stars_balance']
        }
    return {'ton': 0, 'stars': 0}

# ===== ФУНКЦИИ ИНВЕНТАРЯ =====

def add_to_inventory(user_id, gift_id, gift_name=None, quantity=1):
    """Добавить предмет в инвентарь"""
    conn = get_connection()
    cursor = conn.cursor()
    
    user_id_str = str(user_id)
    
    # Проверить, есть ли уже этот подарок
    cursor.execute('''
        SELECT quantity FROM inventory 
        WHERE user_id = ? AND gift_id = ?
    ''', (user_id_str, gift_id))
    
    row = cursor.fetchone()
    
    if row:
        # Увеличить количество
        cursor.execute('''
            UPDATE inventory 
            SET quantity = quantity + ?
            WHERE user_id = ? AND gift_id = ?
        ''', (quantity, user_id_str, gift_id))
    else:
        # Добавить новый подарок
        cursor.execute('''
            INSERT INTO inventory (user_id, gift_id, gift_name, quantity)
            VALUES (?, ?, ?, ?)
        ''', (user_id_str, gift_id, gift_name or f'Gift {gift_id}', quantity))
    
    conn.commit()
    logger.info(f"[DB] Added {quantity}x gift {gift_id} to user {user_id_str}")

def get_inventory(user_id):
    """Получить инвентарь пользователя"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM inventory 
        WHERE user_id = ?
        ORDER BY added_at DESC
    ''', (str(user_id),))
    
    rows = cursor.fetchall()
    return [dict(row) for row in rows]

def remove_from_inventory(user_id, gift_id, quantity=1):
    """Удалить предмет из инвентаря"""
    conn = get_connection()
    cursor = conn.cursor()
    
    user_id_str = str(user_id)
    
    cursor.execute('''
        UPDATE inventory 
        SET quantity = quantity - ?
        WHERE user_id = ? AND gift_id = ?
    ''', (quantity, user_id_str, gift_id))
    
    # Удалить предмет если количество = 0
    cursor.execute('''
        DELETE FROM inventory 
        WHERE user_id = ? AND gift_id = ? AND quantity <= 0
    ''', (user_id_str, gift_id))
    
    conn.commit()
    logger.info(f"[DB] Removed {quantity}x gift {gift_id} from user {user_id_str}")

# ===== ФУНКЦИИ ПРОМОКОДОВ =====

def create_promo_code(code, reward_ton=0, reward_stars=0, uses_limit=1, expires_at=None):
    """Создать промокод"""
    conn = get_connection()
    cursor = conn.cursor()
    
    code_upper = str(code).upper()
    
    cursor.execute('''
        INSERT OR REPLACE INTO promo_codes 
        (code, reward_ton, reward_stars, uses_limit, expires_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (code_upper, reward_ton, reward_stars, uses_limit, expires_at))
    
    conn.commit()
    logger.info(f"[DB] Created promo code: {code_upper}")

def get_promo_code(code):
    """Получить промокод"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM promo_codes 
        WHERE code = ? AND is_active = 1
    ''', (str(code).upper(),))
    
    row = cursor.fetchone()
    return dict(row) if row else None

def use_promo_code(user_id, code):
    """Использовать промокод"""
    conn = get_connection()
    cursor = conn.cursor()
    
    user_id_str = str(user_id)
    code_upper = str(code).upper()
    
    # Проверить, не использовал ли уже этот код
    cursor.execute('''
        SELECT id FROM used_promos 
        WHERE user_id = ? AND code = ?
    ''', (user_id_str, code_upper))
    
    if cursor.fetchone():
        return {'error': 'Already used'}
    
    # Получить промокод
    promo = get_promo_code(code_upper)
    if not promo:
        return {'error': 'Invalid code'}
    
    if not promo['is_active']:
        return {'error': 'Code inactive'}
    
    if promo['uses_count'] >= promo['uses_limit']:
        return {'error': 'Code limit exceeded'}
    
    if promo['expires_at'] and promo['expires_at'] < datetime.now().isoformat():
        return {'error': 'Code expired'}
    
    # Добавить запись об использовании
    cursor.execute('''
        INSERT INTO used_promos (user_id, code)
        VALUES (?, ?)
    ''', (user_id_str, code_upper))
    
    # Увеличить счётчик использований
    cursor.execute('''
        UPDATE promo_codes 
        SET uses_count = uses_count + 1
        WHERE code = ?
    ''', (code_upper,))
    
    # Добавить награду
    if promo['reward_ton'] > 0:
        update_user_balance(user_id_str, promo['reward_ton'], 'TON')
    if promo['reward_stars'] > 0:
        update_user_balance(user_id_str, promo['reward_stars'], 'STARS')
    
    conn.commit()
    logger.info(f"[DB] User {user_id_str} used promo {code_upper}")
    
    return {'success': True, 'reward_ton': promo['reward_ton'], 'reward_stars': promo['reward_stars']}

# ===== ФУНКЦИИ ПОПОЛНЕНИЙ =====

def record_topup(user_id, amount, currency='TON', tx_hash=None):
    """Записать пополнение"""
    conn = get_connection()
    cursor = conn.cursor()
    
    user_id_str = str(user_id)
    
    if currency == 'TON':
        cursor.execute('''
            INSERT INTO topups (user_id, amount, currency, ton_tx_hash, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id_str, amount, currency, tx_hash, 'completed'))
    else:  # STARS
        cursor.execute('''
            INSERT INTO topups (user_id, amount, currency, stars_tx_hash, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id_str, amount, currency, tx_hash, 'completed'))
    
    conn.commit()
    
    # Обновить баланс
    update_user_balance(user_id_str, amount, currency)
    
    logger.info(f"[DB] Recorded {amount} {currency} topup for user {user_id_str}")

def get_topup_history(user_id, limit=50):
    """Получить историю пополнений"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM topups 
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT ?
    ''', (str(user_id), limit))
    
    rows = cursor.fetchall()
    return [dict(row) for row in rows]

# ===== ФУНКЦИИ ВЫВОДОВ =====

def record_withdrawal(user_id, amount, currency='TON', status='pending'):
    """Записать заявку на вывод"""
    conn = get_connection()
    cursor = conn.cursor()
    
    user_id_str = str(user_id)
    
    cursor.execute('''
        INSERT INTO withdrawals (user_id, amount, currency, status)
        VALUES (?, ?, ?, ?)
    ''', (user_id_str, amount, currency, status))
    
    conn.commit()
    logger.info(f"[DB] Created withdrawal request: {amount} {currency} from {user_id_str}")
    
    return cursor.lastrowid

def get_withdrawal_history(user_id, limit=50):
    """Получить историю выводов"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM withdrawals 
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT ?
    ''', (str(user_id), limit))
    
    rows = cursor.fetchall()
    return [dict(row) for row in rows]

def get_all_pending_withdrawals():
    """Получить все ожидающие выводы"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT w.*, u.tg_id, u.tg_name
        FROM withdrawals w
        JOIN users u ON w.user_id = u.user_id
        WHERE w.status = 'pending'
        ORDER BY w.created_at ASC
    ''')
    
    rows = cursor.fetchall()
    return [dict(row) for row in rows]

def update_withdrawal_status(withdrawal_id, status, tx_hash=None):
    """Обновить статус вывода"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE withdrawals 
        SET status = ?, completed_at = CURRENT_TIMESTAMP, ton_tx_hash = ?
        WHERE id = ?
    ''', (status, tx_hash, withdrawal_id))
    
    conn.commit()
    logger.info(f"[DB] Updated withdrawal {withdrawal_id} status to {status}")

# ===== ФУНКЦИИ ТРАНЗАКЦИЙ =====

def add_transaction(user_id, type, amount, currency='TON', description=None):
    """Добавить запись о транзакции"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO transactions (user_id, type, amount, currency, description)
        VALUES (?, ?, ?, ?, ?)
    ''', (str(user_id), type, amount, currency, description))
    
    conn.commit()

def get_transaction_history(user_id, limit=100):
    """Получить историю транзакций"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM transactions 
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT ?
    ''', (str(user_id), limit))
    
    rows = cursor.fetchall()
    return [dict(row) for row in rows]

# ===== ФУНКЦИИ РЕФЕРАЛОВ =====

def get_referrals(user_id):
    """Получить рефералов пользователя"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT r.*, u.tg_name, u.created_at
        FROM referrals r
        JOIN users u ON r.referral_id = u.user_id
        WHERE r.referrer_id = ?
        ORDER BY r.created_at DESC
    ''', (str(user_id),))
    
    rows = cursor.fetchall()
    return [dict(row) for row in rows]

def get_referral_earnings(user_id):
    """Получить заработок от рефералов"""
    user = get_user(str(user_id))
    return user['referral_earnings'] if user else 0

def add_referral_earnings(user_id, amount):
    """Добавить заработок от реферала"""
    conn = get_connection()
    cursor = conn.cursor()
    
    user_id_str = str(user_id)
    
    cursor.execute('''
        UPDATE users 
        SET referral_earnings = referral_earnings + ?
        WHERE user_id = ?
    ''', (amount, user_id_str))
    
    conn.commit()

# ===== ФУНКЦИИ МАРКЕТА =====

def record_market_action(user_id, action, gift_id, gift_name, quantity, price_per_unit, total_price):
    """Записать действие на маркете"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO market_history 
        (user_id, gift_id, gift_name, action, quantity, price_per_unit, total_price)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (str(user_id), gift_id, gift_name, action, quantity, price_per_unit, total_price))
    
    conn.commit()
    logger.info(f"[DB] Recorded market action: {action} {quantity}x {gift_name}")

def get_market_history(user_id, limit=50):
    """Получить историю действий на маркете"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM market_history 
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT ?
    ''', (str(user_id), limit))
    
    rows = cursor.fetchall()
    return [dict(row) for row in rows]

# ===== СЛУЖЕБНЫЕ ФУНКЦИИ =====

def get_stats():
    """Получить статистику БД"""
    conn = get_connection()
    cursor = conn.cursor()
    
    stats = {}
    
    cursor.execute('SELECT COUNT(*) FROM users')
    stats['total_users'] = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM topups WHERE status = "completed"')
    stats['completed_topups'] = cursor.fetchone()[0]
    
    cursor.execute('SELECT SUM(amount) FROM topups WHERE status = "completed" AND currency = "TON"')
    stats['total_ton_topups'] = cursor.fetchone()[0] or 0
    
    cursor.execute('SELECT SUM(amount) FROM withdrawals WHERE status = "completed"')
    stats['completed_withdrawals'] = cursor.fetchone()[0] or 0
    
    cursor.execute('SELECT COUNT(*) FROM withdrawals WHERE status = "pending"')
    stats['pending_withdrawals'] = cursor.fetchone()[0]
    
    return stats

def close_connection():
    """Закрыть соединение с БД"""
    global _connection
    if _connection:
        _connection.close()
        _connection = None
        logger.info("[DB] Connection closed")

# Инициализировать БД при импорте
init_db()
