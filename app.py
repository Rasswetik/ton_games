from flask import Flask, render_template, jsonify, request, redirect, send_from_directory
import os
import json
import logging
from datetime import datetime
from pathlib import Path
import uuid

# Импортируем встроенные 114 подарков для работы на хостинге
try:
    from gifts_data import EMBEDDED_GIFTS
except ImportError:
    EMBEDDED_GIFTS = None

# Импортируем SQLite БД модуль
try:
    import db
    print("[✅] SQLite DB loaded")
    USE_DB = True
except ImportError as e:
    print(f"[WARNING] SQLite DB not available: {e}")
    USE_DB = False

# Импортируем мультиплеер БД
try:
    from multiplayer_db import (
        get_rooms, create_room, get_room, join_room, 
        get_room_players, make_move, update_room_status
    )
    print("[✅] Multiplayer DB loaded")
except ImportError as e:
    print(f"[WARNING] Multiplayer DB not available: {e}")
    get_rooms = None
    get_room = None
    get_room_players = None
    create_room = None
    join_room = None
    make_move = None
    update_room_status = None

# ===== ДИАГНОСТИКА =====
DIAGNOSTIC_LOG_FILE = Path('data/diagnostic_log.json')

def init_diagnostic():
    """Инициализировать диагностический лог"""
    DIAGNOSTIC_LOG_FILE.parent.mkdir(exist_ok=True)
    if not DIAGNOSTIC_LOG_FILE.exists():
        with open(DIAGNOSTIC_LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                'app_start_time': datetime.now().isoformat(),
                'events': [],
                'stats': {'total_starts': 1, 'total_restarts': 0}
            }, f, ensure_ascii=False, indent=2)
    
    log_diagnostic_event('app_startup', {'time': datetime.now().isoformat()})

def log_diagnostic_event(event_type, data=None):
    """Логировать событие диагностики"""
    try:
        DIAGNOSTIC_LOG_FILE.parent.mkdir(exist_ok=True)
        
        if not DIAGNOSTIC_LOG_FILE.exists():
            with open(DIAGNOSTIC_LOG_FILE, 'w', encoding='utf-8') as f:
                json.dump({
                    'app_start_time': datetime.now().isoformat(),
                    'events': [],
                    'stats': {'total_starts': 1, 'total_restarts': 0}
                }, f, ensure_ascii=False, indent=2)
        
        with open(DIAGNOSTIC_LOG_FILE, 'r', encoding='utf-8') as f:
            log_data = json.load(f)
        
        log_data['events'].append({
            'timestamp': datetime.now().isoformat(),
            'type': event_type,
            'data': data or {}
        })
        
        # Ограничить размер логов
        if len(log_data['events']) > 1000:
            log_data['events'] = log_data['events'][-1000:]
        
        with open(DIAGNOSTIC_LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[DIAGNOSTIC] Error: {e}")

# ===== ИНИЦИАЛИЗАЦИЯ ПРИЛОЖЕНИЯ =====
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')

# ===== КОНФИГУРАЦИЯ ПРИЛОЖЕНИЯ =====
ADMIN_IDS = [7679909245, 5257227756]
TELEGRAM_BOT_TOKEN = "8614240590:AAFcQVs8HvyY7jIo0noP_9dGNtS_zEkSMGI"
TELEGRAM_BOT_USERNAME = os.environ.get('TELEGRAM_BOT_USERNAME', 'rpsgames_robot')

# TON Wallet Configuration
TON_RECEIVER_ADDRESS = os.environ.get('TON_RECEIVER_ADDRESS', 'UQDw7-rC3VhNeN5VUjV_Kz5TVBJ5pX4EEI_OOSdU8J0oQkOh')  # Replace with your actual TON wallet address

# ===== ХРАНИЛИЩЕ ДАННЫХ В JSON =====
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

USERS_FILE = DATA_DIR / "users.json"
PROMOS_FILE = DATA_DIR / "promos.json"
WITHDRAWALS_FILE = DATA_DIR / "withdrawals.json"

def load_users():
    """Загрузить пользователей из JSON"""
    if USERS_FILE.exists():
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_users(data):
    """Сохранить пользователей в JSON"""
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_promos():
    """Загрузить промокоды из JSON"""
    if PROMOS_FILE.exists():
        with open(PROMOS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_promos(data):
    """Сохранить промокоды в JSON"""
    with open(PROMOS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_withdrawals():
    """Загрузить заявки на вывод из JSON"""
    if WITHDRAWALS_FILE.exists():
        with open(WITHDRAWALS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'requests': [], 'completed': []}

def save_withdrawals(data):
    """Сохранить заявки на вывод в JSON"""
    with open(WITHDRAWALS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Загрузить данные при старте
user_data = load_users()
promo_codes = load_promos()
# Normalize promo keys to uppercase for consistent lookup
if isinstance(promo_codes, dict):
    normalized = {}
    for k, v in promo_codes.items():
        try:
            normalized[str(k).upper()] = v
        except Exception:
            normalized[k] = v
    promo_codes = normalized
withdrawals_data = load_withdrawals()

def load_gifts():
    """Загрузить подарки из JSON или встроенных данных"""
    try:
        # Сначала пробуем загрузить из файла
        with open('static/data/gifts.json', 'r', encoding='utf-8') as f:
            gifts = json.load(f)
            if gifts and len(gifts) > 0:
                print(f"[GIFTS] [OK] Загружено {len(gifts)} подарков из файла")
                return gifts
    except Exception as e:
        print(f"[GIFTS] [WARNING] Не удалось загрузить из файла: {e}")
    
    # Если файл не найден или пуст - используем встроенные данные
    if EMBEDDED_GIFTS and len(EMBEDDED_GIFTS) > 0:
        print(f"[GIFTS] [OK] Используются встроенные 114 подарков")
        return EMBEDDED_GIFTS
    
    # Fallback на 4 подарка если ничего не нашлось
    print(f"[GIFTS] [WARNING] Подарки не найдены, используем fallback")
    return []

GIFTS = load_gifts()

# Инициализировать диагностику
init_diagnostic()

def get_user_data(user_id, tg_id=None, referred_by=None, tg_name=None):
    """Получить данные пользователя (создать если нет)"""
    user_id_str = str(user_id)
    if user_id_str not in user_data:
        user_data[user_id_str] = {
            'balance': 0,
            'inventory': [],
            'is_new': True,
            'tg_id': tg_id,
            'tg_name': tg_name or 'User',
            'created_at': datetime.now().isoformat(),
            'history': [],
            'referred_by': referred_by,
            'referrals': [],
            'referral_earnings': 0
        }
        save_users(user_data)
    return user_data[user_id_str]

# ===== СТРАНИЦЫ =====

@app.route('/api/admin/check', methods=['GET'])
def check_admin():
    """Проверить является ли пользователь админом"""
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({'status': 'error', 'error': 'user_id required', 'is_admin': False}), 400
        
        user_id_int = int(user_id)
        is_admin = user_id_int in ADMIN_IDS
        
        return jsonify({
            'status': 'ok',
            'user_id': user_id,
            'is_admin': is_admin,
            'admin_ids': ADMIN_IDS
        })
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e), 'is_admin': False}), 500

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/market')
def market():
    return render_template('market.html')

@app.route('/crafts')
def crafts():
    return render_template('crafts.html')

@app.route('/profile')
def profile():
    return render_template('profile.html')

@app.route('/inventory')
def inventory():
    return render_template('inventory.html')

@app.route('/bot')
def bot():
    return render_template('bot.html')

@app.route('/admin')
def admin_panel():
    """Админ панель"""
    return render_template('admin.html')

@app.route('/multiplayer')
def multiplayer():
    """Страница мультиплеера"""
    return render_template('multiplayer.html')

@app.route('/game')
def game():
    """Страница игры в мультиплеере"""
    room_id = request.args.get('room_id')
    if not room_id:
        return redirect('/multiplayer')
    return render_template('game.html', room_id=room_id)

# ===== MULTIPLAYER API ====

@app.route('/api/ton/init', methods=['POST'])
def ton_init():
    """Инициализация пользователя"""
    try:
        data = request.json
        user_id = str(data.get('user_id'))
        tg_id = data.get('tg_id')
        
        if not user_id:
            return jsonify({'error': 'user_id required'}), 400
        
        # Получить или создать пользователя
        user = get_user_data(user_id, tg_id)
        
        # Создать простой токен
        token = str(uuid.uuid4())
        
        return jsonify({
            'status': 'ok',
            'token': token,
            'is_admin': int(user_id) in ADMIN_IDS,
            'is_new': user['is_new']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ton/connect', methods=['POST'])
def ton_connect():
    """Подключение кошелька"""
    try:
        data = request.json
        user_id = str(data.get('user_id'))
        address = data.get('address')
        
        if not user_id or not address:
            return jsonify({'error': 'user_id and address required'}), 400
        
        user = get_user_data(user_id)
        user['history'].append({
            'action': 'wallet_connected',
            'timestamp': datetime.now().isoformat(),
            'address': address
        })
        save_users(user_data)
        
        return jsonify({
            'status': 'connected',
            'user_id': user_id,
            'address': address
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ton/disconnect', methods=['POST'])
def ton_disconnect():
    """Отключение кошелька"""
    try:
        data = request.json
        user_id = str(data.get('user_id'))
        
        user = get_user_data(user_id)
        user['history'].append({
            'action': 'wallet_disconnected',
            'timestamp': datetime.now().isoformat()
        })
        save_users(user_data)
        
        return jsonify({'status': 'disconnected'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ton/balance/<user_id>', methods=['GET'])
def get_balance(user_id):
    """Получить баланс пользователя"""
    try:
        user = get_user_data(user_id)
        return jsonify({
            'user_id': user_id,
            'balance': user['balance'],
            'inventory_count': len(user['inventory'])
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ton/send-transaction', methods=['POST'])
def send_transaction():
    """Отправить транзакцию"""
    try:
        data = request.json
        user_id = str(data.get('user_id'))
        recipient = data.get('recipient')
        amount = data.get('amount')
        
        if not all([user_id, recipient, amount]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        return jsonify({
            'status': 'pending',
            'tx_hash': f'0x{"0"*64}',
            'user_id': user_id,
            'recipient': recipient,
            'amount': amount
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== ПОЛЬЗОВАТЕЛЬСКИЙ API =====

@app.route('/api/user/data/<user_id>', methods=['GET'])
def get_user_info(user_id):
    """Получить данные пользователя"""
    try:
        user = get_user_data(user_id)
        return jsonify({
            'user_id': user_id,
            'balance': user['balance'],
            'inventory': user['inventory'],
            'is_new': user['is_new'],
            'is_admin': int(user_id) in ADMIN_IDS
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/update', methods=['POST'])
def update_user():
    """Обновить данные пользователя"""
    try:
        data = request.json
        user_id = str(data.get('user_id'))
        balance = data.get('balance')
        inventory = data.get('inventory')
        is_new = data.get('is_new')
        
        if not user_id:
            return jsonify({'error': 'user_id required'}), 400
        
        user = get_user_data(user_id)
        
        if balance is not None:
            user['balance'] = balance
        if inventory is not None:
            user['inventory'] = inventory
        if is_new is not None:
            user['is_new'] = is_new
        
        save_users(user_data)
        
        return jsonify({'status': 'updated'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== КРАФТ API =====

def find_gift_by_price(target_price):
    """Найти подарок ближайший по цене к target_price"""
    if not GIFTS:
        return None
    
    # Найти подарок с самой близкой ценой
    closest_gift = None
    min_diff = float('inf')
    
    for gift in GIFTS:
        price = gift.get('price', 0)
        diff = abs(price - target_price)
        
        if diff < min_diff:
            min_diff = diff
            closest_gift = gift
    
    return closest_gift

@app.route('/api/gifts/list', methods=['GET'])
def gifts_list():
    """Получить список всех подарков"""
    try:
        return jsonify({
            'status': 'ok',
            'count': len(GIFTS),
            'gifts': GIFTS,
            'gift_ids': [g['id'] for g in GIFTS]
        })
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/gift/buy', methods=['POST'])
def buy_gift():
    """Купить подарок на маркете"""
    try:
        data = request.json
        user_id = str(data.get('user_id'))
        gift_id = str(data.get('gift_id')).lower().strip()
        
        if not user_id or not gift_id:
            return jsonify({'status': 'error', 'error': 'user_id and gift_id required'}), 400
        
        # Найти подарок по ID
        gift = next((g for g in GIFTS if g['id'].lower() == gift_id.lower()), None)
        if not gift:
            return jsonify({'status': 'error', 'error': f'Gift {gift_id} not found'}), 404
        
        # Получить или создать пользователя
        user = get_user_data(user_id)
        gift_price = float(gift.get('price', 0))
        
        # Проверить баланс
        if user['balance'] < gift_price:
            return jsonify({
                'status': 'error', 
                'error': f'Not enough balance. Required: {gift_price} TON, have: {user["balance"]} TON'
            }), 400
        
        # Вычесть стоимость и добавить подарок в инвентарь
        user['balance'] -= gift_price
        user['inventory'].append(gift['id'])
        
        # Добавить бонус реферреру если есть
        if user.get('referred_by'):
            referrer_id = user['referred_by']
            referrer = get_user_data(referrer_id)
            referral_bonus = gift_price * 0.1  # 10% от покупки
            referrer['balance'] += referral_bonus
            referrer['referral_earnings'] += referral_bonus
            referrer['history'].append({
                'action': 'referral_bonus',
                'from_user': user_id,
                'amount': referral_bonus,
                'timestamp': datetime.now().isoformat()
            })
            save_users(user_data)
        
        # Добавить в историю
        user['history'].append({
            'action': 'gift_purchased',
            'gift_id': gift['id'],
            'gift_name': gift['name'],
            'price': gift_price,
            'timestamp': datetime.now().isoformat()
        })
        
        save_users(user_data)
        
        print(f"[PURCHASE] User {user_id} bought {gift['name']} for {gift_price} TON. New balance: {user['balance']}")
        
        return jsonify({
            'status': 'ok',
            'message': f'Gift \"{gift["name"]}\" purchased successfully',
            'gift_id': gift['id'],
            'gift_name': gift['name'],
            'price': gift_price,
            'new_balance': user['balance']
        })
    except Exception as e:
        print(f"[PURCHASE ERROR] {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/craft', methods=['POST'])
def craft_items():
    """Скомбинировать предметы в один подарок"""
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({'status': 'error', 'error': 'user_id required'}), 400
        
        data = request.json
        item_ids = data.get('items', [])
        
        if not item_ids or len(item_ids) < 3:
            return jsonify({'status': 'error', 'error': 'Нужно минимум 3 предмета'}), 400
        
        user = get_user_data(user_id)
        
        # Найти подарки по ID и проверить их наличие
        selected_gifts = []
        total_price = 0
        indices_to_remove = []
        
        for item_id in item_ids:
            # Найти подарок в GIFTS
            gift = next((g for g in GIFTS if g['id'] == item_id), None)
            if not gift:
                return jsonify({'status': 'error', 'error': f'Подарок {item_id} не найден'}), 400
            
            selected_gifts.append(gift)
            total_price += gift.get('price', 0)
            
            # Найти и пометить в инвентаре для удаления - берем ПЕРВЫЙ найденный экземпляр
            found = False
            for idx, inv_item in enumerate(user['inventory']):
                if idx in indices_to_remove:
                    continue  # Пропускаем уже помеченные
                    
                inv_item_id = inv_item if isinstance(inv_item, str) else inv_item.get('id', inv_item.get('name'))
                if inv_item_id == item_id:
                    indices_to_remove.append(idx)
                    found = True
                    break
            
            if not found:
                return jsonify({'status': 'error', 'error': f'Предмет {item_id} не в инвентаре'}), 400
        
        # Удалить выбранные предметы из инвентаря (в обратном порядке чтобы индексы не сдвигались)
        for idx in sorted(indices_to_remove, reverse=True):
            user['inventory'].pop(idx)
        
        # Выбрать подарок БЛИЖЕйший по цене к потраченной сумме
        import random
        
        if not GIFTS:
            return jsonify({'status': 'error', 'error': 'Не удалось найти подарок'}), 500
        
        # Фильтровать подарки в диапазоне 50%-150% от потраченной суммы
        similar_price_gifts = []
        min_price = total_price * 0.5
        max_price = total_price * 1.5
        
        for gift in GIFTS:
            gift_price = gift.get('price', 0)
            if min_price <= gift_price <= max_price:
                similar_price_gifts.append(gift)
        
        # Если есть подарки в диапазоне - выбрать из них
        if similar_price_gifts:
            result_gift = random.choice(similar_price_gifts)
        else:
            # Если нет в диапазоне - найти ближайший по цене
            result_gift = min(GIFTS, key=lambda g: abs(g.get('price', 0) - total_price))
        
        # Добавить новый подарок в инвентарь (как ID строку)
        user['inventory'].append(result_gift['id'])
        
        # Сохранить
        save_users(user_data)
        
        # Получить цену подарка для отображения
        reward_value = result_gift.get('price', 0)
        
        print(f"[CRAFT] User {user_id}: crafted {len(selected_gifts)} items (total: {total_price}) -> {result_gift['name']} ({reward_value})")
        
        return jsonify({
            'status': 'ok',
            'result_gift': result_gift,
            'reward': reward_value,
            'message': f"Получен {result_gift['name']}!"
        })
    except Exception as e:
        print(f"[CRAFT] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/craft/sell', methods=['POST'])
def craft_sell():
    """Продать полученный подарок из крафта"""
    try:
        data = request.json
        user_id = data.get('user_id')
        gift_id = data.get('gift_id')
        reward = data.get('reward')
        
        if not user_id or not reward or not gift_id:
            return jsonify({'status': 'error', 'error': 'user_id, gift_id and reward required'}), 400
        
        user = get_user_data(user_id)
        
        # Remove gift from inventory
        if gift_id in user['inventory']:
            user['inventory'].remove(gift_id)
        
        # Add reward to balance
        user['balance'] += reward
        
        save_users(user_data)
        
        return jsonify({
            'status': 'ok',
            'new_balance': user['balance']
        })
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/user/sell-all', methods=['POST'])
def sell_all_gifts():
    """Продать список подарков по ID"""
    try:
        data = request.json
        user_id = str(data.get('user_id'))
        gift_ids = data.get('gift_ids', [])
        
        if not user_id or not gift_ids:
            return jsonify({'status': 'error', 'error': 'user_id and gift_ids required'}), 400
        
        user = get_user_data(user_id)
        
        # Проверить, нет ли pending запросов на вывод для этих подарков
        for gift_id in gift_ids:
            pending_req = next((r for r in withdrawals_data['requests'] if r['gift_id'] == gift_id and r['status'] == 'pending'), None)
            if pending_req:
                return jsonify({'status': 'error', 'error': f'Cannot sell: gift has pending withdrawal request'}), 400
        
        # Посчитать сумму продажи
        total_price = 0
        for gift_id in gift_ids:
            gift = next((g for g in GIFTS if g['id'] == gift_id), None)
            if gift:
                total_price += gift.get('price', 0)
                # Удалить подарок из инвентаря
                if gift_id in user['inventory']:
                    user['inventory'].remove(gift_id)
        
        # Добавить баланс
        user['balance'] += total_price
        
        # Сохранить
        save_users(user_data)
        
        return jsonify({
            'status': 'ok',
            'sold_amount': total_price,
            'new_balance': user['balance']
        })
    except Exception as e:
        print(f"[SELL] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'error': str(e)}), 500


@app.route('/api/user/sell-instance', methods=['POST'])
def sell_instance():
    """Sell a single inventory instance by index"""
    try:
        data = request.json
        user_id = str(data.get('user_id'))
        inv_index = data.get('inventory_index')

        if user_id is None or inv_index is None:
            return jsonify({'status': 'error', 'error': 'user_id and inventory_index required'}), 400

        user = get_user_data(user_id)

        try:
            idx = int(inv_index)
        except Exception:
            return jsonify({'status': 'error', 'error': 'invalid inventory_index'}), 400

        if idx < 0 or idx >= len(user['inventory']):
            return jsonify({'status': 'error', 'error': 'inventory_index out of range'}), 400

        # Check pending withdrawal specifically for this instance
        pending_req = next((r for r in withdrawals_data['requests'] if r['user_id'] == user_id and r['status'] == 'pending' and r.get('inventory_index') == idx), None)
        if pending_req:
            return jsonify({'status': 'error', 'error': 'Cannot sell: this instance has a pending withdrawal request'}), 400

        # Determine gift id at that inventory index
        inv_item = user['inventory'][idx]
        gift_id = inv_item if isinstance(inv_item, str) else inv_item.get('id')
        gift = next((g for g in GIFTS if g['id'] == gift_id), None)
        price = float(gift.get('price', 0)) if gift else 0

        # Remove this inventory entry
        user['inventory'].pop(idx)
        user['balance'] += price
        save_users(user_data)

        return jsonify({'status': 'ok', 'sold_amount': price, 'new_balance': user['balance']})
    except Exception as e:
        print(f"[SELL INSTANCE] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'error': str(e)}), 500

# ===== GIFT WITHDRAWAL API =====

@app.route('/api/user/request-withdrawal', methods=['POST'])
def request_gift_withdrawal():
    """Запросить вывод подарка"""
    try:
        global withdrawals_data, user_data
        
        data = request.json
        user_id = str(data.get('user_id'))
        gift_id = data.get('gift_id')
        gift_name = data.get('gift_name')
        inventory_index = data.get('inventory_index')
        
        if not user_id or not gift_id:
            return jsonify({'status': 'error', 'error': 'user_id and gift_id required'}), 400
        
        # Получить пользователя
        user = get_user_data(user_id)
        
        # Проверить наличие подарка в инвентаре
        # If inventory items may be objects, normalize check
        inv_ids = [it if isinstance(it, str) else it.get('id', None) for it in user['inventory']]
        if gift_id not in inv_ids:
            return jsonify({'status': 'error', 'error': 'Gift not in inventory'}), 400
        
        # Проверить, нет ли уже pending запроса для этого конкретного экземпляра (если указан индекс)
        if inventory_index is not None:
            existing_request = next((r for r in withdrawals_data['requests'] if r['gift_id'] == gift_id and r['user_id'] == user_id and r['status'] == 'pending' and r.get('inventory_index') == int(inventory_index)), None)
            if existing_request:
                return jsonify({'status': 'error', 'error': 'This inventory instance already has a pending withdrawal request'}), 400
        else:
            # If no index provided, disallow if any pending request exists for this gift type for the user
            existing_request = next((r for r in withdrawals_data['requests'] if r['gift_id'] == gift_id and r['user_id'] == user_id and r['status'] == 'pending'), None)
            if existing_request:
                return jsonify({'status': 'error', 'error': 'Gift already has pending withdrawal request'}), 400
        
        # Подарок ОСТАЁТСЯ в инвентаре, будет удалён только при одобрении
        print(f"[WITHDRAWAL REQUEST] Gift {gift_id} for user {user_id} will be removed on approve")
        
        # Создать заявку на вывод (подарок ещё в инвентаре)
        withdrawal_request = {
            'request_id': f"wd_{uuid.uuid4().hex[:8]}",
            'user_id': user_id,
            'username': user.get('username', 'User'),
            'tg_name': user.get('tg_name', user.get('username', 'User')),
            'gift_id': gift_id,
            'gift_name': gift_name,
            'inventory_index': int(inventory_index) if inventory_index is not None else None,
            'status': 'pending',
            'created_at': datetime.now().isoformat(),
            'approved_at': None,
            'approved_by': None
        }
        
        # Добавить в requests
        withdrawals_data['requests'].append(withdrawal_request)
        save_withdrawals(withdrawals_data)
        print(f"[WITHDRAWAL REQUEST] Created withdrawal request for gift {gift_id}, gift stays in inventory")
        
        return jsonify({
            'status': 'ok',
            'message': 'Withdrawal request created',
            'request_id': withdrawal_request['request_id']
        })
    except Exception as e:
        print(f"[WITHDRAWAL] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/admin/withdrawals', methods=['GET'])
def admin_get_withdrawals():
    """Получить заявки на вывод (только админ)"""
    try:
        user_id = str(request.args.get('user_id'))
        
        if int(user_id) not in ADMIN_IDS:
            return jsonify({'error': 'Admin only'}), 403
        
        return jsonify({
            'status': 'ok',
            'pending_requests': [r for r in withdrawals_data['requests'] if r['status'] == 'pending'],
            'completed_requests': withdrawals_data['completed']
        })
    except Exception as e:
        print(f"[ADMIN] Error: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/admin/withdrawal/approve', methods=['POST'])
def admin_approve_withdrawal():
    """Одобрить заявку на вывод (только админ)"""
    try:
        global withdrawals_data, user_data
        
        data = request.json
        admin_id = data.get('admin_id')
        request_id = data.get('request_id')

        if admin_id is None:
            return jsonify({'status': 'error', 'error': 'admin_id required'}), 400

        try:
            admin_int = int(admin_id)
        except Exception:
            return jsonify({'status': 'error', 'error': 'invalid admin_id'}), 400

        if admin_int not in ADMIN_IDS:
            return jsonify({'status': 'error', 'error': 'Admin only'}), 403
        
        # Найти заявку
        withdrawal_req = next((r for r in withdrawals_data['requests'] if r['request_id'] == request_id), None)
        if not withdrawal_req:
            return jsonify({'status': 'error', 'error': 'Request not found'}), 404
        
        # ТЕПЕРЬ удалить подарок из инвентаря при одобрении
        user = get_user_data(withdrawal_req['user_id'])
        # If the request specified an inventory_index, try to remove that specific instance
        inv_idx = withdrawal_req.get('inventory_index')
        removed = False
        if inv_idx is not None:
            try:
                idx = int(inv_idx)
                if 0 <= idx < len(user['inventory']):
                    # Remove the specific inventory entry by index
                    popped = user['inventory'].pop(idx)
                    save_users(user_data)
                    removed = True
                    print(f"[WITHDRAWAL APPROVE] Removed inventory index {idx} (item {popped}) from user {withdrawal_req['user_id']}")
                    # Adjust other pending requests' inventory_index for this user
                    for r in withdrawals_data['requests']:
                        if r['user_id'] == withdrawal_req['user_id'] and r.get('inventory_index') is not None:
                            try:
                                ri = int(r['inventory_index'])
                                if ri > idx:
                                    r['inventory_index'] = ri - 1
                            except Exception:
                                pass
                    save_withdrawals(withdrawals_data)
                    removed_index = idx
            except Exception:
                removed = False

        # Fallback: if not removed by index, remove first occurrence by gift_id
        if not removed:
            # Fallback: remove first occurrence by gift_id and adjust pending indexes accordingly
            if withdrawal_req['gift_id'] in user['inventory']:
                # Find index of first occurrence
                found_idx = None
                for i, inv_item in enumerate(user['inventory']):
                    inv_id = inv_item if isinstance(inv_item, str) else inv_item.get('id')
                    if inv_id == withdrawal_req['gift_id']:
                        found_idx = i
                        break

                if found_idx is not None:
                    popped = user['inventory'].pop(found_idx)
                    save_users(user_data)
                    print(f"[WITHDRAWAL APPROVE] Removed gift {withdrawal_req['gift_id']} from inventory at index {found_idx} (fallback)")
                    # Adjust other pending requests' inventory_index for this user
                    for r in withdrawals_data['requests']:
                        if r['user_id'] == withdrawal_req['user_id'] and r.get('inventory_index') is not None:
                            try:
                                ri = int(r['inventory_index'])
                                if ri > found_idx:
                                    r['inventory_index'] = ri - 1
                            except Exception:
                                pass
                    save_withdrawals(withdrawals_data)
                    removed_index = found_idx
        
        # Обновить заявку
        withdrawal_req['status'] = 'approved'
        withdrawal_req['approved_at'] = datetime.now().isoformat()
        withdrawal_req['approved_by'] = str(admin_int)
        
        # Переместить в completed
        withdrawals_data['requests'].remove(withdrawal_req)
        withdrawals_data['completed'].append(withdrawal_req)
        
        # СОХРАНИТЬ
        save_withdrawals(withdrawals_data)
        print(f"[WITHDRAWAL APPROVE] Request {request_id} approved by {admin_id}")
        
        resp = {'status': 'ok', 'message': 'Withdrawal approved', 'gift_name': withdrawal_req.get('gift_name')}
        if 'removed_index' in locals():
            resp['removed_index'] = removed_index
        return jsonify(resp)
    except Exception as e:
        print(f"[ADMIN] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/admin/withdrawal/reject', methods=['POST'])
def admin_reject_withdrawal():
    """Отклонить заявку на вывод (только админ) - подарок остаётся в инвентаре"""
    try:
        global withdrawals_data, user_data
        
        data = request.json
        admin_id = data.get('admin_id')
        request_id = data.get('request_id')

        if admin_id is None:
            return jsonify({'status': 'error', 'error': 'admin_id required'}), 400

        try:
            admin_int = int(admin_id)
        except Exception:
            return jsonify({'status': 'error', 'error': 'invalid admin_id'}), 400

        if admin_int not in ADMIN_IDS:
            return jsonify({'status': 'error', 'error': 'Admin only'}), 403
        
        # Найти заявку
        withdrawal_req = next((r for r in withdrawals_data['requests'] if r['request_id'] == request_id), None)
        if not withdrawal_req:
            return jsonify({'status': 'error', 'error': 'Request not found'}), 404
        
        # Обновить заявку (подарок уже в инвентаре, ничего не трогаем)
        withdrawal_req['status'] = 'rejected'
        withdrawal_req['approved_at'] = datetime.now().isoformat()
        withdrawal_req['approved_by'] = str(admin_int)
        
        # Переместить в completed
        withdrawals_data['requests'].remove(withdrawal_req)
        withdrawals_data['completed'].append(withdrawal_req)
        
        save_withdrawals(withdrawals_data)
        print(f"[WITHDRAWAL REJECT] Request {request_id} rejected, gift {withdrawal_req['gift_id']} stays in inventory")
        
        return jsonify({
            'status': 'ok',
            'message': 'Withdrawal rejected, gift returned to inventory'
        })
    except Exception as e:
        print(f"[ADMIN] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/user/pending-withdrawals', methods=['GET'])
def get_user_pending_withdrawals():
    """Получить pending запросы на вывод для пользователя"""
    try:
        user_id = str(request.args.get('user_id'))
        
        if not user_id:
            return jsonify({'error': 'user_id required'}), 400
        
        # Найти все pending запросы для этого пользователя
        pending = [r for r in withdrawals_data['requests'] if r['user_id'] == user_id and r['status'] == 'pending']

        # Вернуть список gift_id с pending запросами и подробные записи (включая inventory_index, если есть)
        pending_gift_ids = [r['gift_id'] for r in pending]
        pending_requests = []
        for r in pending:
            pending_requests.append({
                'request_id': r.get('request_id'),
                'gift_id': r.get('gift_id'),
                'inventory_index': r.get('inventory_index') if 'inventory_index' in r else None,
                'created_at': r.get('created_at')
            })

        return jsonify({
            'status': 'ok',
            'pending_gift_ids': pending_gift_ids,
            'pending_requests': pending_requests,
            'pending_count': len(pending)
        })
    except Exception as e:
        print(f"[PENDING WITHDRAWALS] Error: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500

# ===== ПРОМОКОДЫ API =====

@app.route('/api/promo/create', methods=['POST'])
def create_promo():
    """Создать промокод"""
    try:
        data = request.json
        user_id = str(data.get('user_id'))
        
        if int(user_id) not in ADMIN_IDS:
            return jsonify({'error': 'Admin only'}), 403
        
        promo_name = data.get('promo_name')
        reward_type = data.get('reward_type')
        reward_amount = data.get('reward_amount')
        reward_gift = data.get('reward_gift')
        max_activations = data.get('max_activations', 100)
        
        if not promo_name or not reward_type:
            return jsonify({'error': 'Missing fields'}), 400
        
        if promo_name in promo_codes:
            return jsonify({'error': 'Promo already exists'}), 400
        
        promo_codes[promo_name] = {
            'type': reward_type,
            'reward_amount': reward_amount,
            'reward_gift': reward_gift,
            'max_activations': max_activations,
            'activations': 0,
            'created_at': datetime.now().isoformat(),
            'used_by': []
        }
        save_promos(promo_codes)
        
        return jsonify({
            'status': 'created',
            'promo_name': promo_name,
            'activation_link': f"https://rpsgames.pythonanywhere.com/promo/{promo_name}",
            'telegram_link': f"https://t.me/{TELEGRAM_BOT_USERNAME}?start=promo_{promo_name}"
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/promo/activate/<promo_name>/<user_id>', methods=['GET'])
def activate_promo_link(promo_name, user_id):
    """Активировать промокод через ссылку"""
    try:
        user_id = str(user_id)
        
        if not user_id or not promo_name:
            return jsonify({'error': 'Missing fields'}), 400
        promo_key = promo_name.upper()
        if promo_key not in promo_codes:
            return jsonify({'error': 'Promo not found'}), 404
        promo = promo_codes[promo_key]
        
        if promo['activations'] >= promo['max_activations']:
            return jsonify({'error': 'Promo limit reached'}), 400
        
        if user_id in promo['used_by']:
            return jsonify({'error': 'Already used'}), 400
        
        user = get_user_data(user_id)
        reward_text = ""
        reward_display = {}
        
        if promo['type'] == 'balance':
            user['balance'] += promo['reward_amount']
            reward_text = f"+{promo['reward_amount']} TON"
            reward_display = {
                'type': 'balance',
                'amount': promo['reward_amount'],
                'text': reward_text
            }
        elif promo['type'] == 'gift':
            user['inventory'].append({
                'id': promo['reward_gift'],
                'name': promo['reward_gift'],
                'timestamp': datetime.now().isoformat()
            })
            
            # Получить информацию о подарке
            gift = next((g for g in GIFTS if g['id'] == promo['reward_gift']), None)
            reward_display = {
                'type': 'gift',
                'gift_id': promo['reward_gift'],
                'name': gift['name'] if gift else promo['reward_gift'],
                'image': gift['image'] if gift else '',
                'text': f"+1 {gift['name'] if gift else promo['reward_gift']}"
            }
            reward_text = f"+1 {gift['name'] if gift else promo['reward_gift']}"
        
        # Обновить промокод
        promo['activations'] += 1
        promo['used_by'].append(user_id)
        
        # Добавить в историю
        user['history'].append({
            'action': 'promo_activated',
            'promo': promo_name,
            'reward': reward_text,
            'timestamp': datetime.now().isoformat()
        })
        
        save_users(user_data)
        save_promos(promo_codes)
        
        return jsonify({
            'status': 'activated',
            'reward': reward_display,
            'new_balance': user['balance'],
            'message': f'🎉 Промокод активирован! Вы получили {reward_text}'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/promo/activate', methods=['POST'])
def activate_promo():
    """Активировать промокод через POST"""
    try:
        data = request.json
        user_id = str(data.get('user_id'))
        promo_name = data.get('promo_name')
        
        if not user_id or not promo_name:
            return jsonify({'error': 'Missing fields'}), 400
        promo_key = promo_name.upper()
        if promo_key not in promo_codes:
            return jsonify({'error': 'Promo not found'}), 404
        promo = promo_codes[promo_key]
        
        if promo['activations'] >= promo['max_activations']:
            return jsonify({'error': 'Promo limit reached'}), 400
        
        if user_id in promo['used_by']:
            return jsonify({'error': 'Already used'}), 400
        
        user = get_user_data(user_id)
        reward_text = ""
        
        if promo['type'] == 'balance':
            user['balance'] += promo['reward_amount']
            reward_text = f"+{promo['reward_amount']} TON"
        elif promo['type'] == 'gift':
            user['inventory'].append({
                'id': promo['reward_gift'],
                'name': promo['reward_gift'],
                'timestamp': datetime.now().isoformat()
            })
            reward_text = f"+1 {promo['reward_gift']}"
        
        promo['activations'] += 1
        promo['used_by'].append(user_id)
        
        user['history'].append({
            'action': 'promo_activated',
            'promo': promo_name,
            'reward': reward_text,
            'timestamp': datetime.now().isoformat()
        })
        
        save_users(user_data)
        save_promos(promo_codes)
        
        return jsonify({
            'status': 'activated',
            'reward': reward_text,
            'new_balance': user['balance'],
            'new_inventory_count': len(user['inventory'])
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/promo/delete', methods=['POST'])
def delete_promo():
    """Удалить промокод"""
    try:
        data = request.json
        user_id = str(data.get('user_id'))
        promo_name = data.get('promo_name')
        
        if int(user_id) not in ADMIN_IDS:
            return jsonify({'error': 'Admin only'}), 403
        
        if promo_name in promo_codes:
            del promo_codes[promo_name]
            save_promos(promo_codes)
            return jsonify({'status': 'deleted'})
        
        return jsonify({'error': 'Promo not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== АДМИН API - ПОЛЬЗОВАТЕЛИ =====

@app.route('/api/admin/users', methods=['GET'])
def admin_get_users():
    """Получить список пользователей"""
    try:
        user_id = request.args.get('user_id')
        
        if int(user_id) not in ADMIN_IDS:
            return jsonify({'error': 'Admin only'}), 403
        
        users = []
        for uid, data in user_data.items():
            users.append({
                'user_id': uid,
                'balance': data['balance'],
                'inventory_count': len(data['inventory']),
                'is_new': data['is_new'],
                'created_at': data['created_at'],
                'history_count': len(data['history'])
            })
        
        return jsonify({'users': users})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/user/<target_user_id>', methods=['GET'])
def admin_get_user_details(target_user_id):
    """Получить детали пользователя"""
    try:
        user_id = request.args.get('user_id')
        
        if int(user_id) not in ADMIN_IDS:
            return jsonify({'error': 'Admin only'}), 403
        
        if target_user_id not in user_data:
            return jsonify({'error': 'User not found'}), 404
        
        user = user_data[target_user_id]
        
        return jsonify({
            'user_id': target_user_id,
            'tg_name': user.get('tg_name', 'User'),
            'balance': user['balance'],
            'inventory': user['inventory'],
            'is_new': user['is_new'],
            'created_at': user['created_at'],
            'history': user['history']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/user/edit', methods=['POST'])
def admin_edit_user():
    """Редактировать пользователя"""
    try:
        data = request.json
        admin_id = str(data.get('admin_id'))
        target_user_id = str(data.get('user_id'))
        new_balance = data.get('balance')
        new_inventory = data.get('inventory')
        
        if int(admin_id) not in ADMIN_IDS:
            return jsonify({'error': 'Admin only'}), 403
        
        user = get_user_data(target_user_id)
        
        if new_balance is not None:
            old_balance = user['balance']
            user['balance'] = new_balance
            user['history'].append({
                'action': 'balance_edited_by_admin',
                'admin_id': admin_id,
                'old_balance': old_balance,
                'new_balance': new_balance,
                'timestamp': datetime.now().isoformat()
            })
        
        if new_inventory is not None:
            user['inventory'] = new_inventory
            user['history'].append({
                'action': 'inventory_edited_by_admin',
                'admin_id': admin_id,
                'timestamp': datetime.now().isoformat()
            })
        
        save_users(user_data)
        
        return jsonify({'status': 'updated'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== АДМИН API - ПОДАРКИ =====

@app.route('/api/admin/gifts', methods=['GET'])
def admin_get_gifts():
    """Получить список подарков"""
    try:
        user_id = request.args.get('user_id')
        
        if int(user_id) not in ADMIN_IDS:
            return jsonify({'error': 'Admin only'}), 403
        
        return jsonify({'gifts': GIFTS})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/gift/add', methods=['POST'])
def admin_add_gift():
    """Добавить новый подарок"""
    try:
        data = request.json
        admin_id = str(data.get('admin_id'))
        
        if int(admin_id) not in ADMIN_IDS:
            return jsonify({'error': 'Admin only'}), 403
        
        new_gift = {
            'id': data.get('id'),
            'name': data.get('name'),
            'price': data.get('price'),
            'image': data.get('image')
        }
        
        GIFTS.append(new_gift)
        
        with open('static/data/gifts.json', 'w', encoding='utf-8') as f:
            json.dump(GIFTS, f, ensure_ascii=False, indent=2)
        
        return jsonify({'status': 'added', 'gift': new_gift})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/gift/edit', methods=['POST'])
def admin_edit_gift():
    """Редактировать подарок"""
    try:
        data = request.json
        admin_id = str(data.get('admin_id'))
        gift_id = data.get('gift_id')
        
        if int(admin_id) not in ADMIN_IDS:
            return jsonify({'error': 'Admin only'}), 403
        
        for gift in GIFTS:
            if gift['id'] == gift_id:
                gift['name'] = data.get('name', gift['name'])
                gift['price'] = data.get('price', gift['price'])
                gift['image'] = data.get('image', gift['image'])
                break
        
        with open('static/data/gifts.json', 'w', encoding='utf-8') as f:
            json.dump(GIFTS, f, ensure_ascii=False, indent=2)
        
        return jsonify({'status': 'updated'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== HEALTH CHECK =====

@app.route('/api/multiplayer/rooms', methods=['GET'])
def get_multiplayer_rooms():
    """Получить список всех доступных комнат"""
    try:
        # Очистить пустые комнаты перед каждым запросом
        try:
            from multiplayer_db import cleanup_empty_rooms
            cleanup_empty_rooms(timeout_seconds=120)  # 2 минуты
        except:
            pass
        
        if not get_rooms or not get_room_players:
            return jsonify({'status': 'ok', 'count': 0, 'rooms': []}), 200
        
        rooms = get_rooms('waiting')
        
        # Добавить информацию об игроках для каждой комнаты
        rooms_with_players = []
        for room in rooms:
            try:
                players = get_room_players(room['room_id'])
                room['players'] = players
                rooms_with_players.append(room)
            except Exception as e:
                print(f"[WARNING] Error loading room {room['room_id']}: {e}")
                room['players'] = []
                rooms_with_players.append(room)
        
        return jsonify({
            'status': 'ok',
            'count': len(rooms_with_players),
            'rooms': rooms_with_players
        })
    except Exception as e:
        print(f"[❌] Error: {e}")
        return jsonify({'status': 'ok', 'count': 0, 'rooms': []}), 200

@app.route('/api/multiplayer/create-room', methods=['POST'])
def create_multiplayer_room():
    """Создать новую комнату"""
    try:
        if not create_room:
            return jsonify({'status': 'error', 'error': 'Multiplayer not available'}), 503
        
        data = request.json
        stake = float(data.get('stake', 1.0))
        players = int(data.get('players', 2))
        rounds = int(data.get('rounds', 3))
        
        # Валидация
        if stake < 0.5 or stake > 100:
            return jsonify({'status': 'error', 'error': 'Invalid stake'}), 400
        
        if players < 2 or players > 5:
            return jsonify({'status': 'error', 'error': 'Invalid player count'}), 400
        
        # Генерировать уникальный ID комнаты
        room_id = f"room_{uuid.uuid4().hex[:8]}"
        
        # Создать комнату
        result = create_room(room_id, stake, 2, players, rounds)
        if result:
            return jsonify({
                'status': 'ok',
                'room_id': room_id,
                'stake': stake,
                'max_players': players,
                'rounds': rounds
            })
        else:
            return jsonify({'status': 'error', 'error': 'Failed to create room'}), 500
    except Exception as e:
        print(f"[❌] Error: {e}")
        return jsonify({'status': 'error', 'error': 'Internal server error'}), 500

@app.route('/api/multiplayer/join-room', methods=['POST'])
def join_multiplayer_room():
    """Присоединиться к комнате"""
    try:
        if not join_room or not get_room:
            return jsonify({'status': 'error', 'error': 'Multiplayer not available'}), 503
        
        data = request.json
        room_id = data.get('room_id')
        user_id = str(data.get('user_id'))
        
        # Получить данные пользователя
        user = get_user_data(user_id)
        
        # Проверить комнату
        room = get_room(room_id)
        if not room:
            return jsonify({'status': 'error', 'error': 'Room not found'}), 404
        
        # Проверить баланс
        if user['balance'] < room['stake']:
            return jsonify({
                'status': 'error', 
                'error': f'Insufficient balance'
            }), 400
        
        # Присоединиться
        tg_user = data.get('username', 'Player')
        avatar = data.get('avatar_url', '')
        
        result = join_room(room_id, user_id, tg_user, avatar, user['balance'])
        if result:
            return jsonify({
                'status': 'ok',
                'message': 'Joined room',
                'room_id': room_id
            })
        else:
            return jsonify({'status': 'error', 'error': 'Failed to join room'}), 500
    except Exception as e:
        print(f"[❌] Error: {e}")
        return jsonify({'status': 'error', 'error': 'Internal server error'}), 500

@app.route('/api/multiplayer/room/<room_id>', methods=['GET'])
def get_multiplayer_room(room_id):
    """Получить информацию о комнате"""
    try:
        if not get_room or not get_room_players:
            return jsonify({'status': 'error', 'error': 'Multiplayer not available'}), 503
        
        room = get_room(room_id)
        if not room:
            return jsonify({'status': 'error', 'error': 'Room not found'}), 404
        
        players = get_room_players(room_id)
        room['players'] = players
        
        return jsonify({
            'status': 'ok',
            'room': room
        })
    except Exception as e:
        print(f"[❌] Error: {e}")
        return jsonify({'status': 'error', 'error': 'Internal server error'}), 500

@app.route('/api/multiplayer/make-move', methods=['POST'])
def make_multiplayer_move():
    """Сделать ход (камень, ножницы, бумага)"""
    try:
        if not make_move:
            return jsonify({'status': 'error', 'error': 'Multiplayer not available'}), 503
        
        data = request.json
        room_id = data.get('room_id')
        user_id = str(data.get('user_id'))
        choice = data.get('choice')  # 'rock', 'scissors', 'paper'
        round_number = int(data.get('round_number', 1))
        
        if choice not in ['rock', 'scissors', 'paper']:
            return jsonify({'status': 'error', 'error': 'Invalid choice'}), 400
        
        if make_move(room_id, user_id, choice, round_number):
            return jsonify({
                'status': 'ok',
                'message': 'Move recorded'
            })
        else:
            return jsonify({'status': 'error', 'error': 'Failed to record move'}), 500
    except Exception as e:
        print(f"[❌] Error: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500

# ===== HEALTH CHECK =====

@app.route('/tonconnect-manifest.json')
def tonconnect_manifest():
    """Serve TonConnect 2.0 manifest with proper configuration"""
    try:
        # Try to serve manifest file from root
        manifest_path = Path('tonconnect-manifest.json')
        if manifest_path.exists():
            with open(manifest_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return app.response_class(
                content,
                mimetype='application/json',
                headers={
                    'Cache-Control': 'no-cache, no-store, must-revalidate',
                    'Pragma': 'no-cache',
                    'Expires': '0'
                }
            )
    except Exception as e:
        app.logger.error('Failed to read tonconnect-manifest.json: %s', e)

    # Fallback: return TonConnect 2.0 compliant manifest
    return jsonify({
        "tonconnect": {
            "version": 2
        },
        "app": {
            "name": "RPS Games",
            "description": "Rock Paper Scissors Game with TON Connect 2.0",
            "url": "https://rpsgames.pythonanywhere.com",
            "icons": [
                "https://rpsgames.pythonanywhere.com/static/img/icon.png"
            ]
        },
        "notification": {
            "enabled": False
        }
    })


@app.route('/static/vendor/tonconnect-ui.min.js')
def serve_tonconnect_vendor():
    """Serve local TonConnect UI vendor file (explicit route to avoid static mapping issues)."""
    try:
        return send_from_directory('static/vendor', 'tonconnect-ui.min.js')
    except Exception as e:
        app.logger.error('Failed to serve TonConnect vendor file: %s', e)
        return ('', 404)

@app.route('/api/ton/wallet-address', methods=['GET'])
def get_wallet_address():
    """Get receiver wallet address for TON payments"""
    return jsonify({
        'status': 'ok',
        'receiver_address': TON_RECEIVER_ADDRESS,
        'network': 'mainnet'
    })

@app.route('/api/referral/link/<user_id>', methods=['GET'])
def get_referral_link(user_id):
    """Get referral link for user"""
    try:
        user = get_user_data(user_id)
        referral_link = f"https://t.me/{TELEGRAM_BOT_USERNAME}?start=ref_{user_id}"
        return jsonify({
            'status': 'ok',
            'referral_link': referral_link,
            'referrals_count': len(user.get('referrals', [])),
            'referral_earnings': user.get('referral_earnings', 0)
        })
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/referral/join', methods=['POST'])
def join_referral():
    """Join referral program"""
    try:
        data = request.json
        new_user_id = str(data.get('user_id'))
        referrer_id = str(data.get('referrer_id'))
        
        if not new_user_id or not referrer_id:
            return jsonify({'status': 'error', 'error': 'Missing fields'}), 400
        
        # Get or create new user with referrer
        new_user = get_user_data(new_user_id, referred_by=referrer_id)
        
        # Add to referrer's list
        referrer = get_user_data(referrer_id)
        if new_user_id not in referrer.get('referrals', []):
            if 'referrals' not in referrer:
                referrer['referrals'] = []
            referrer['referrals'].append(new_user_id)
        
        save_users(user_data)
        
        return jsonify({
            'status': 'ok',
            'message': 'Referral link activated'
        })
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/user/referral-info/<user_id>', methods=['GET'])
def get_referral_info(user_id):
    """Get referral info for user"""
    try:
        user = get_user_data(user_id)
        return jsonify({
            'status': 'ok',
            'referrals_count': len(user.get('referrals', [])),
            'referral_earnings': user.get('referral_earnings', 0),
            'referred_by': user.get('referred_by')
        })
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500


# ===== REFERRAL CODES (per-user promo codes) =====
@app.route('/api/referral/code/<user_id>', methods=['GET'])
def get_referral_code(user_id):
    try:
        user = get_user_data(user_id)
        code = user.get('referral_code')
        # Generate default code if missing
        if not code:
            import random, string
            for _ in range(10):
                candidate = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
                if not any(u.get('referral_code', '') == candidate for u in user_data.values()):
                    code = candidate
                    user['referral_code'] = code
                    save_users(user_data)
                    break
            if not code:
                code = ('CODE' + str(user.get('created_at', '')))[-8:]
                user['referral_code'] = code
                save_users(user_data)

        return jsonify({
            'status': 'ok',
            'referral_code': code,
            'referrals_count': len(user.get('referrals', [])),
            'referral_earnings': user.get('referral_earnings', 0)
        })
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500


@app.route('/api/referral/code', methods=['POST'])
def set_referral_code():
    try:
        data = request.json
        user_id = str(data.get('user_id'))
        code = (data.get('code') or '').strip().upper()

        if not user_id or not code:
            return jsonify({'status': 'error', 'error': 'Missing fields'}), 400

        # Ensure uniqueness
        for uid, u in user_data.items():
            if uid != user_id and u.get('referral_code', '').upper() == code:
                return jsonify({'status': 'error', 'error': 'Code already in use'}), 400

        user = get_user_data(user_id)
        user['referral_code'] = code
        save_users(user_data)

        return jsonify({'status': 'ok', 'referral_code': code})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500


@app.route('/api/referral/redeem', methods=['POST'])
def redeem_referral_code():
    try:
        data = request.json
        user_id = str(data.get('user_id'))
        code = (data.get('code') or '').strip().upper()

        if not user_id or not code:
            return jsonify({'status': 'error', 'error': 'Missing fields'}), 400

        # Find referrer by code
        referrer_id = None
        for uid, u in user_data.items():
            if u.get('referral_code', '').upper() == code:
                referrer_id = uid
                break

        if not referrer_id:
            return jsonify({'status': 'error', 'error': 'Code not found'}), 404

        if referrer_id == user_id:
            return jsonify({'status': 'error', 'error': 'Cannot use your own code'}), 400

        new_user = get_user_data(user_id)
        if new_user.get('referred_by'):
            return jsonify({'status': 'error', 'error': 'User already referred'}), 400

        # Apply reward to the new user
        reward_amount = 0.1
        new_user['balance'] = new_user.get('balance', 0) + reward_amount
        new_user['referred_by'] = referrer_id
        new_user['history'].append({
            'action': 'referral_redeemed',
            'by_code': code,
            'referrer': referrer_id,
            'reward': f'+{reward_amount} TON',
            'timestamp': datetime.now().isoformat()
        })

        # Update referrer record
        ref = get_user_data(referrer_id)
        if 'referrals' not in ref:
            ref['referrals'] = []
        if user_id not in ref['referrals']:
            ref['referrals'].append(user_id)

        save_users(user_data)

        # Prepare referrer stats to return so frontend can immediately update UI
        referrer_stats = {
            'referrer_id': referrer_id,
            'referrer_referrals_count': len(ref.get('referrals', [])),
            'referrer_referral_earnings': ref.get('referral_earnings', 0)
        }

        return jsonify({
            'status': 'ok',
            'message': f'Referral applied. +{reward_amount} TON',
            'new_balance': new_user['balance'],
            'referrer': referrer_stats
        })
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

# ===== ПОЛЬЗОВАТЕЛЬСКИЙ API - НОВЫЕ МАРШРУТЫ =====

@app.route('/api/user/get', methods=['GET'])
def get_user():
    """Получить данные пользователя"""
    try:
        user_id = str(request.args.get('user_id'))
        
        if not user_id:
            return jsonify({'error': 'user_id required'}), 400
        
        if USE_DB:
            user_db = db.get_user(user_id)
            if not user_db:
                # Создать нового пользователя
                user_db = db.create_or_get_user(user_id)
            balance = user_db['balance']
            inventory = user_db.get('inventory', [])
        else:
            user = get_user_data(user_id)
            balance = user['balance']
            inventory = user['inventory']
        
        return jsonify({
            'status': 'ok',
            'balance': float(balance),
            'inventory': inventory,
            'created_at': user_db.get('created_at') if USE_DB else user.get('created_at')
        })
    except Exception as e:
        print(f"[ERROR] get_user failed: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ===== ПРОМОКОДЫ API =====

@app.route('/api/promo/list', methods=['GET'])
def get_promos_list():
    """Получить список всех промокодов"""
    try:
        promos_list = list(promo_codes.values())
        return jsonify({
            'status': 'ok',
            'promos': promos_list
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== АДМИН API - ПРОМОКОДЫ =====

@app.route('/api/admin/promo/create', methods=['POST'])
def admin_create_promo():
    """Создать промокод (только для админов)"""
    try:
        data = request.json
        user_id = str(data.get('user_id'))
        
        if int(user_id) not in ADMIN_IDS:
            return jsonify({'error': 'Admin only', 'status': 'error'}), 403
        
        name = data.get('name', '').upper()
        reward = data.get('reward', {})
        max_activations = data.get('max_activations', 1)
        
        if not name or len(name) < 3:
            return jsonify({'error': 'Invalid name', 'status': 'error'}), 400
        
        if name in promo_codes:
            return jsonify({'error': 'Promo already exists', 'status': 'error'}), 400
        
        promo_codes[name] = {
            'name': name,
            'reward': reward,
            'max_activations': max_activations,
            'activations': 0,
            'used_by': [],
            'created_at': datetime.now().isoformat(),
            'created_by': user_id
        }
        
        save_promos(promo_codes)
        
        return jsonify({'status': 'ok', 'message': f'Промокод {name} создан'})
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500

@app.route('/api/admin/promo/delete', methods=['GET'])
def admin_delete_promo():
    """Удалить промокод (только для админов)"""
    try:
        user_id = str(request.args.get('user_id'))
        name = request.args.get('name', '').upper()
        
        if int(user_id) not in ADMIN_IDS:
            return jsonify({'error': 'Admin only', 'status': 'error'}), 403
        
        if name in promo_codes:
            del promo_codes[name]
            save_promos(promo_codes)
            return jsonify({'status': 'ok', 'message': f'Промокод {name} удален'})
        else:
            return jsonify({'error': 'Promo not found', 'status': 'error'}), 404
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500

# ===== АДМИН API - ПОЛЬЗОВАТЕЛИ =====

@app.route('/api/admin/user/balance', methods=['POST'])
def admin_update_balance():
    """Обновить баланс пользователя (только для админов)"""
    try:
        data = request.json
        user_id = str(data.get('user_id'))
        target_user_id = str(data.get('target_user_id'))
        balance = data.get('balance')
        
        if int(user_id) not in ADMIN_IDS:
            return jsonify({'error': 'Admin only', 'status': 'error'}), 403
        
        user = get_user_data(target_user_id)
        user['balance'] = balance
        user['history'].append({
            'action': 'balance_edited_by_admin',
            'admin_id': user_id,
            'value': balance,
            'timestamp': datetime.now().isoformat()
        })
        save_users(user_data)
        
        return jsonify({'status': 'ok', 'message': f'Баланс обновлён'})
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500

# ===== GAME RESULT API =====

@app.route('/api/game/result', methods=['POST'])
def save_game_result():
    """Save bot game result and update balance"""
    try:
        data = request.json
        user_id = str(data.get('user_id'))
        player_choice = data.get('player_choice')
        bot_choice = data.get('bot_choice')
        amount = data.get('amount')  # win amount (can be negative for loss)
        bet = data.get('bet')
        
        if not user_id or amount is None:
            return jsonify({'status': 'error', 'error': 'Missing fields'}), 400
        
        user = get_user_data(user_id)
        
        # Update balance
        user['balance'] += amount
        
        # Ensure balance doesn't go negative
        if user['balance'] < 0:
            user['balance'] = 0
        
        # Record history
        result_type = 'win' if amount > 0 else ('draw' if amount == 0 else 'loss')
        user['history'].append({
            'action': 'bot_game',
            'result': result_type,
            'player_choice': player_choice,
            'bot_choice': bot_choice,
            'bet': bet,
            'amount': amount,
            'new_balance': user['balance'],
            'timestamp': datetime.now().isoformat()
        })
        
        save_users(user_data)
        
        return jsonify({
            'status': 'ok',
            'new_balance': user['balance'],
            'message': f'Balance updated: {result_type}'
        })
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

# ===== BOT API ENDPOINTS (для внешних ботов на других хостингах) =====

@app.route('/api/bot/users', methods=['GET'])
def bot_get_users():
    """Получить список всех пользователей (для бота)"""
    try:
        users_list = []
        for user_id, user_data_item in user_data.items():
            users_list.append({
                'user_id': user_id,
                'username': user_data_item.get('username', 'User'),
                'tg_name': user_data_item.get('tg_name', 'User'),
                'tg_id': user_data_item.get('tg_id'),
                'balance': user_data_item.get('balance', 0),
                'inventory_count': len(user_data_item.get('inventory', [])),
                'referrals_count': len(user_data_item.get('referrals', [])),
                'created_at': user_data_item.get('created_at')
            })
        
        return jsonify({
            'status': 'ok',
            'total': len(users_list),
            'users': users_list
        })
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/bot/user/<user_id>', methods=['GET'])
def bot_get_user(user_id):
    """Получить данные одного пользователя (для бота)"""
    try:
        user = get_user_data(str(user_id))
        
        if not user:
            return jsonify({'status': 'error', 'error': 'User not found'}), 404
        
        return jsonify({
            'status': 'ok',
            'user_id': user_id,
            'username': user.get('username', 'User'),
            'tg_name': user.get('tg_name', 'User'),
            'tg_id': user.get('tg_id'),
            'balance': user.get('balance', 0),
            'inventory': user.get('inventory', []),
            'referrals': user.get('referrals', []),
            'referral_earnings': user.get('referral_earnings', 0),
            'created_at': user.get('created_at'),
            'referred_by': user.get('referred_by')
        })
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/bot/gifts', methods=['GET'])
def bot_get_gifts():
    """Получить список всех подарков (для бота)"""
    try:
        gifts_list = []
        for gift_id, gift_data in GIFTS.items():
            gifts_list.append({
                'id': gift_id,
                'name': gift_data.get('name'),
                'description': gift_data.get('description'),
                'price': gift_data.get('price'),
                'image': gift_data.get('image'),
                'rarity': gift_data.get('rarity')
            })
        
        return jsonify({
            'status': 'ok',
            'total': len(gifts_list),
            'gifts': gifts_list
        })
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/bot/promos', methods=['GET'])
def bot_get_promos():
    """Получить список промокодов (для бота)"""
    try:
        promos_list = []
        for promo_code, promo_data in promo_codes.items():
            promos_list.append({
                'code': promo_code,
                'bonus': promo_data.get('bonus'),
                'uses': promo_data.get('uses', 0),
                'max_uses': promo_data.get('max_uses'),
                'expires_at': promo_data.get('expires_at')
            })
        
        return jsonify({
            'status': 'ok',
            'total': len(promos_list),
            'promos': promos_list
        })
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

# ===== TELEGRAM BOT INTEGRATION =====
# NOTE: Bot is NOT started on production (Render)
# Bot must run locally with: python bot_run_local.py
# This prevents asyncio conflicts with Flask/Gunicorn
print("[ℹ️] Telegram Bot disabled on production - run locally with: python bot_run_local.py")

# ===== TELEGRAM STARS API =====

# Exchange rate: 1 Star = 0.01 TON (configurable)
TELEGRAM_STARS_TO_TON_RATE = 0.01
TELEGRAM_BOT_TOKEN = '8614240590:AAFcQVs8HvyY7jIo0noP_9dGNtS_zEkSMGI'  # Bot token
TELEGRAM_BOT_USERNAME = 'rpsgames_robot'  # Bot username

@app.route('/api/create-stars-invoice', methods=['POST'])
def create_stars_invoice():
    """Создать инвойс для оплаты Telegram Stars с retry-логикой"""
    try:
        data = request.json
        user_id = str(data.get('user_id', 'anonymous'))
        stars_amount = int(data.get('stars_amount', 1))
        
        if stars_amount <= 0:
            return jsonify({'success': False, 'error': 'Invalid amount'}), 400
        
        # Конвертировать звёзды в TON для информации
        ton_equivalent = stars_amount * TELEGRAM_STARS_TO_TON_RATE
        invoice_id = f"stars_{uuid.uuid4().hex[:8]}"
        
        print(f"\n[STARS] ========== CREATE INVOICE START ==========")
        print(f"[STARS] User: {user_id}, Stars: {stars_amount}, Invoice ID: {invoice_id}")
        
        # Попытка вызвать Telegram API с retry
        if TELEGRAM_BOT_TOKEN:
            import requests
            max_retries = 3
            retry_delay = 1
            
            for attempt in range(1, max_retries + 1):
                try:
                    print(f"[STARS] Attempt {attempt}/{max_retries} to call Telegram API...")
                    
                    payload = {
                        'title': f'Пополнение баланса: {stars_amount} Stars',
                        'description': f'{stars_amount} Telegram Stars для пополнения игрового баланса',
                        'payload': invoice_id,
                        'currency': 'XTR',
                        'prices': [{'label': f'{stars_amount} Stars', 'amount': stars_amount}]
                    }
                    
                    response = requests.post(
                        f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/createInvoiceLink',
                        json=payload,
                        timeout=5  # Reduce timeout for faster failure
                    )
                    
                    print(f"[STARS] Bot API response: status={response.status_code}")
                    
                    if response.status_code == 200:
                        invoice_data = response.json()
                        
                        if invoice_data.get('ok') and invoice_data.get('result'):
                            invoice_link = invoice_data.get('result')
                            print(f"[STARS] ✅ SUCCESS! Invoice link: {invoice_link[:80]}...")
                            print(f"[STARS] ========== CREATE INVOICE END (SUCCESS) ==========\n")
                            
                            return jsonify({
                                'success': True,
                                'invoice_id': invoice_id,
                                'stars_amount': stars_amount,
                                'ton_equivalent': ton_equivalent,
                                'invoice_link': invoice_link,
                                'currency': 'XTR'
                            })
                        else:
                            err_desc = invoice_data.get('description', 'Unknown error')
                            print(f"[STARS] ❌ Bot API error: {err_desc}")
                            if attempt < max_retries:
                                print(f"[STARS] Retrying in {retry_delay}s...")
                                import time
                                time.sleep(retry_delay)
                                retry_delay *= 2  # Exponential backoff
                            continue
                    else:
                        print(f"[STARS] ❌ Bot API HTTP error: {response.status_code}")
                        if attempt < max_retries:
                            print(f"[STARS] Retrying in {retry_delay}s...")
                            import time
                            time.sleep(retry_delay)
                            retry_delay *= 2
                        continue
                        
                except requests.exceptions.Timeout:
                    print(f"[STARS] ⚠️ Timeout on attempt {attempt}")
                    if attempt < max_retries:
                        print(f"[STARS] Retrying in {retry_delay}s...")
                        import time
                        time.sleep(retry_delay)
                        retry_delay *= 2
                    continue
                    
                except requests.exceptions.ProxyError as e:
                    print(f"[STARS] ⚠️ Proxy error on attempt {attempt}: {str(e)[:100]}")
                    if attempt < max_retries:
                        print(f"[STARS] Retrying in {retry_delay}s...")
                        import time
                        time.sleep(retry_delay)
                        retry_delay *= 2
                    continue
                    
                except Exception as e:
                    print(f"[STARS] ⚠️ Error on attempt {attempt}: {str(e)[:100]}")
                    if attempt < max_retries:
                        print(f"[STARS] Retrying in {retry_delay}s...")
                        import time
                        time.sleep(retry_delay)
                        retry_delay *= 2
                    continue
            
            # Все попытки исчерпаны, используем fallback
            print(f"[STARS] ⚠️ All {max_retries} attempts failed, using FALLBACK mode")
        
        # Fallback: Генерируем synthetic invoice link для тестирования
        # Этот режим позволяет тестировать polling без доступа к Telegram API
        print(f"[STARS] Using OFFLINE FALLBACK - synthetic invoice link")
        synthetic_link = f"https://t.me/{TELEGRAM_BOT_USERNAME}?start=invoice_{invoice_id}"
        
        print(f"[STARS] ========== CREATE INVOICE END (FALLBACK) ==========\n")
        
        return jsonify({
            'success': True,
            'invoice_id': invoice_id,
            'stars_amount': stars_amount,
            'ton_equivalent': ton_equivalent,
            'invoice_link': synthetic_link,
            'currency': 'XTR',
            'warning': 'Telegram API not available, using fallback link'
        })
        
    except Exception as e:
        print(f"[STARS] ❌ Error creating invoice: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/process-stars-payment', methods=['GET', 'POST'])
def process_stars_payment():
    """Обработать платёж Telegram Stars"""
    try:
        if request.method == 'POST':
            data = request.json
            user_id = str(data.get('user_id'))
            invoice_id = data.get('invoice_id')
            stars_amount = int(data.get('stars_amount', 1))
        else:
            user_id = str(request.args.get('user_id'))
            invoice_id = request.args.get('invoice_id')
            stars_amount = int(request.args.get('stars', 1))
        
        if not user_id or not invoice_id:
            print(f"[STARS] Missing params: user_id={user_id}, invoice_id={invoice_id}")
            return jsonify({'success': False, 'error': 'Missing parameters'}), 400
        
        # Конвертировать звёзды в TON
        ton_amount = stars_amount * TELEGRAM_STARS_TO_TON_RATE
        
        print(f"[STARS] Processing payment: user={user_id}, stars={stars_amount}, ton={ton_amount}, invoice={invoice_id}")
        
        # Если используется SQLite
        if USE_DB:
            print(f"[STARS] Using SQLite DB")
            user = db.create_or_get_user(user_id)
            print(f"[STARS] User balance BEFORE: {user.get('balance', 'unknown')}")
            
            db.record_topup(user_id, ton_amount, 'STARS', invoice_id)
            print(f"[STARS] Recorded topup")
            
            balance_dict = db.get_user_balance(user_id)
            print(f"[STARS] Got balance dict: {balance_dict}")
            
            new_balance = balance_dict['ton'] if isinstance(balance_dict, dict) else balance_dict
            print(f"[STARS] Extracted new_balance: {new_balance}")
            
            # Refresh user data to verify
            user_refreshed = db.get_user(user_id)
            print(f"[STARS] Refreshed user balance: {user_refreshed.get('balance', 'unknown') if user_refreshed else 'user not found'}")
        else:
            print(f"[STARS] Using JSON storage")
            user = get_user_data(user_id)
            user['balance'] += ton_amount
            user['history'].append({
                'action': 'stars_topup',
                'amount': ton_amount,
                'stars_amount': stars_amount,
                'invoice_id': invoice_id,
                'timestamp': datetime.now().isoformat()
            })
            save_users(user_data)
            new_balance = user['balance']
        
        print(f"[STARS] ✅ Payment COMPLETE: user={user_id}, added={ton_amount} TON, new_balance={new_balance}")
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'stars_amount': stars_amount,
            'ton_amount': ton_amount,
            'new_balance': float(new_balance),
            'message': f'Спасибо! Вы получили {ton_amount} TON за {stars_amount} Telegram Stars'
        })
    except Exception as e:
        print(f"[STARS] Error processing payment: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stars/balance/<user_id>', methods=['GET'])
def get_stars_balance(user_id):
    """Получить баланс Stars пользователя"""
    try:
        if USE_DB:
            balance = db.get_user_balance(user_id)
            return jsonify({
                'user_id': user_id,
                'ton_balance': balance['ton'],
                'stars_balance': balance['stars']
            })
        else:
            user = get_user_data(user_id)
            return jsonify({
                'user_id': user_id,
                'balance': user.get('balance', 0),
                'stars': user.get('stars_balance', 0)
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stars/validate-bot', methods=['GET'])
def validate_telegram_bot():
    """Проверить, работает ли Bot Token"""
    try:
        import requests
        
        # Test bot token by calling getMe
        response = requests.post(
            f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe',
            timeout=10
        )
        
        if response.status_code == 200:
            bot_info = response.json()
            if bot_info.get('ok'):
                return jsonify({
                    'status': 'ok',
                    'bot_valid': True,
                    'bot_username': bot_info['result'].get('username'),
                    'bot_name': bot_info['result'].get('first_name'),
                    'message': 'Bot Token is valid'
                })
        
        return jsonify({
            'status': 'error',
            'bot_valid': False,
            'response_status': response.status_code,
            'response_text': response.text[:200],
            'message': 'Bot Token validation failed'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'bot_valid': False,
            'error': str(e),
            'message': 'Bot Token test error'
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'app': 'RPS Games',
        'users_count': len(user_data),
        'gifts_count': len(GIFTS),
        'promos_count': len(promo_codes),
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
