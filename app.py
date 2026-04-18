from flask import Flask, render_template, jsonify, request
import os
import json
import logging
from datetime import datetime
from pathlib import Path
import uuid

# ===== ИНИЦИАЛИЗАЦИЯ ПРИЛОЖЕНИЯ =====
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')

# ===== КОНФИГУРАЦИЯ ПРИЛОЖЕНИЯ =====
ADMIN_IDS = [7679909245, 5257227556]
TELEGRAM_BOT_TOKEN = "8614240590:AAFcQVs8HvyY7jIo0noP_9dGNtS_zEkSMGI"

# ===== ХРАНИЛИЩЕ ДАННЫХ В JSON =====
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

USERS_FILE = DATA_DIR / "users.json"
PROMOS_FILE = DATA_DIR / "promos.json"

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

# Загрузить данные при старте
user_data = load_users()
promo_codes = load_promos()

def load_gifts():
    """Загрузить подарки из JSON"""
    try:
        with open('static/data/gifts.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

GIFTS = load_gifts()

def get_user_data(user_id, tg_id=None):
    """Получить данные пользователя (создать если нет)"""
    user_id_str = str(user_id)
    if user_id_str not in user_data:
        user_data[user_id_str] = {
            'balance': 0,
            'inventory': [],
            'is_new': True,
            'tg_id': tg_id,
            'created_at': datetime.now().isoformat(),
            'history': []
        }
        save_users(user_data)
    return user_data[user_id_str]

# ===== СТРАНИЦЫ =====

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

@app.route('/bot')
def bot():
    return render_template('bot.html')

@app.route('/admin_panel')
def admin_panel():
    """Админ панель (только для администраторов)"""
    # В реальном приложении здесь должна быть проверка authentication
    return render_template('admin.html')

# ===== TON CONNECT API =====

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
            'telegram_link': f"https://t.me/rps_game_bot?start=promo_{promo_name}"
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/promo/list', methods=['GET'])
def list_promos():
    """Получить список промокодов (только для админа)"""
    try:
        user_id = request.args.get('user_id')
        
        if int(user_id) not in ADMIN_IDS:
            return jsonify({'error': 'Admin only'}), 403
        
        promos = []
        for promo_name, promo_data in promo_codes.items():
            promos.append({
                'name': promo_name,
                'type': promo_data['type'],
                'reward_amount': promo_data['reward_amount'],
                'reward_gift': promo_data['reward_gift'],
                'activations': f"{promo_data['activations']}/{promo_data['max_activations']}",
                'link': f"https://t.me/rps_game_bot?start=promo_{promo_name}"
            })
        
        return jsonify({'promos': promos})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/promo/activate/<promo_name>/<user_id>', methods=['GET'])
def activate_promo_link(promo_name, user_id):
    """Активировать промокод через ссылку"""
    try:
        user_id = str(user_id)
        
        if not user_id or not promo_name:
            return jsonify({'error': 'Missing fields'}), 400
        
        if promo_name not in promo_codes:
            return jsonify({'error': 'Promo not found'}), 404
        
        promo = promo_codes[promo_name]
        
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
        
        if promo_name not in promo_codes:
            return jsonify({'error': 'Promo not found'}), 404
        
        promo = promo_codes[promo_name]
        
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

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'service': 'RPS Game API'})

# ===== ПОЛЬЗОВАТЕЛЬСКИЙ API - НОВЫЕ МАРШРУТЫ =====

@app.route('/api/user/get', methods=['GET'])
def get_user():
    """Получить данные пользователя"""
    try:
        user_id = str(request.args.get('user_id'))
        
        if not user_id:
            return jsonify({'error': 'user_id required'}), 400
        
        user = get_user_data(user_id)
        return jsonify({
            'status': 'ok',
            'balance': user['balance'],
            'inventory': user['inventory'],
            'is_new': user['is_new'],
            'created_at': user['created_at']
        })
    except Exception as e:
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

@app.route('/api/promo/activate/<promo_name>/<user_id>', methods=['POST'])
def activate_promo(promo_name, user_id):
    """Активировать промокод"""
    try:
        promo_name = promo_name.upper()
        user_id = str(user_id)
        
        if promo_name not in promo_codes:
            return jsonify({'status': 'error', 'message': 'Промокод не найден'}), 404
        
        promo = promo_codes[promo_name]
        user = get_user_data(user_id)
        
        # Проверить максимум активаций
        if promo['activations'] >= promo['max_activations']:
            return jsonify({'status': 'error', 'message': 'Промокод закончился'}), 400
        
        # Проверить уже активировал ли пользователь
        if user_id in promo['used_by']:
            return jsonify({'status': 'error', 'message': 'Вы уже активировали этот промокод'}), 400
        
        # Выдать награду
        if promo['reward']['type'] == 'balance':
            user['balance'] += promo['reward']['amount']
            message = f"Промокод активирован! Вы получили {promo['reward']['amount']} TON"
        else:
            # Получить подарок
            gift_name = promo['reward']['gift']
            user['inventory'].append({'name': gift_name, 'activated_promo': promo_name})
            message = f"Промокод активирован! Вы получили подарок: {gift_name}"
        
        # Обновить промокод
        promo['activations'] += 1
        promo['used_by'].append(user_id)
        
        # Сохранить
        save_users(user_data)
        save_promos(promo_codes)
        
        user['history'].append({
            'action': 'promo_activated',
            'promo': promo_name,
            'timestamp': datetime.now().isoformat()
        })
        
        return jsonify({'status': 'ok', 'message': message})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

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

# ===== TELEGRAM BOT INTEGRATION =====

try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
    
    # Создать приложение Telegram бота
    tg_app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /start"""
        user = update.effective_user
        promo_name = None
        
        # Проверить если это переход с промокода
        if context.args:
            promo_name = context.args[0].upper()
        
        welcome_text = f"👋 Привет, {user.first_name}!\n\n"
        welcome_text += "Добро пожаловать в РПС GAMES! 🎮\n\n"
        welcome_text += "Это игра Камень-Ножницы-Бумага где ты можешь:\n"
        welcome_text += "• 💰 Зарабатывать TON\n"
        welcome_text += "• 🎁 Собирать подарки\n"
        welcome_text += "• 🎯 Участвовать в крафтинге\n\n"
        
        if promo_name and promo_name in promo_codes:
            promo = promo_codes[promo_name]
            if promo['activations'] < promo['max_activations']:
                welcome_text += f"🎁 У тебя есть промокод: {promo_name}\n"
                welcome_text += f"Награда: "
                if promo['reward']['type'] == 'balance':
                    welcome_text += f"+{promo['reward']['amount']} TON\n"
                else:
                    welcome_text += f"подарок: {promo['reward']['gift']}\n"
                welcome_text += "Активируй его в игре!\n\n"
        
        keyboard = [[InlineKeyboardButton("🎮 Открыть игру", url="https://rpsgames.pythonanywhere.com")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    
    # Добавить обработчик команды /start
    tg_app.add_handler(CommandHandler("start", start_command))
    
except Exception as e:
    print(f"⚠️ Telegram Bot error: {e}")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
