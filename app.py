from flask import Flask, render_template, jsonify, request
import os
import jwt
import json
import threading
import logging
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')

# ===== КОНФИГУРАЦИЯ =====
ADMIN_IDS = [7679909245, 5257227756]
TELEGRAM_BOT_TOKEN = "8614240590:AAFcQVs8HvyY7jIo0noP_9dGNtS_zEkSMGI"

# ===== ХРАНИЛИЩЕ ДАННЫХ (в продакшене используйте БД) =====
user_sessions = {}
user_data = {}  # user_id -> {balance, inventory, is_new, tg_id, created_at, history}
promo_codes = {}  # promo_name -> {type, count, remaining, reward_amount, reward_gift}

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
    if user_id not in user_data:
        user_data[user_id] = {
            'balance': 0,
            'inventory': [],
            'is_new': True,  # Новый пользователь
            'tg_id': tg_id,
            'created_at': datetime.now().isoformat(),
            'history': []
        }
    return user_data[user_id]

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

@app.route('/admin')
def admin_panel():
    """Админ панель"""
    return render_template('admin.html')

# ===== TON CONNECT API =====

@app.route('/api/ton/init', methods=['POST'])
def ton_init():
    """Инициализация пользователя"""
    try:
        data = request.json
        user_id = data.get('user_id')
        tg_id = data.get('tg_id')
        
        if not user_id:
            return jsonify({'error': 'user_id required'}), 400
        
        # Инициализируем данные пользователя
        if user_id not in user_data:
            user_data[user_id] = get_user_data(user_id, tg_id)
        
        token = jwt.encode(
            {'user_id': user_id, 'iat': datetime.now()},
            app.config['SECRET_KEY'],
            algorithm='HS256'
        )
        
        user_sessions[user_id] = {
            'token': token,
            'connected': False,
            'address': None,
            'balance': 0
        }
        
        return jsonify({
            'status': 'ok',
            'token': token,
            'is_admin': user_id in ADMIN_IDS,
            'is_new': user_data[user_id]['is_new']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ton/connect', methods=['POST'])
def ton_connect():
    """Подключение кошелька"""
    try:
        data = request.json
        user_id = data.get('user_id')
        address = data.get('address')
        
        if not user_id or not address:
            return jsonify({'error': 'user_id and address required'}), 400
        
        if user_id in user_sessions:
            user_sessions[user_id]['connected'] = True
            user_sessions[user_id]['address'] = address
            
            if user_id not in user_data:
                user_data[user_id] = get_user_data(user_id)
            
            user_data[user_id]['history'].append({
                'action': 'wallet_connected',
                'timestamp': datetime.now().isoformat(),
                'address': address
            })
            
            return jsonify({
                'status': 'connected',
                'user_id': user_id,
                'address': address
            })
        
        return jsonify({'error': 'Session not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ton/disconnect', methods=['POST'])
def ton_disconnect():
    """Отключение кошелька"""
    try:
        data = request.json
        user_id = data.get('user_id')
        
        if user_id in user_sessions:
            user_sessions[user_id]['connected'] = False
            user_sessions[user_id]['address'] = None
            
            return jsonify({'status': 'disconnected'})
        
        return jsonify({'error': 'Session not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ton/balance/<user_id>', methods=['GET'])
def get_balance(user_id):
    """Получить баланс пользователя"""
    try:
        if user_id not in user_data:
            user_data[user_id] = get_user_data(user_id)
        
        user = user_data[user_id]
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
        user_id = data.get('user_id')
        recipient = data.get('recipient')
        amount = data.get('amount')
        
        if not all([user_id, recipient, amount]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        if user_id not in user_sessions or not user_sessions[user_id]['connected']:
            return jsonify({'error': 'Wallet not connected'}), 400
        
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
        if user_id not in user_data:
            user_data[user_id] = get_user_data(user_id)
        
        user = user_data[user_id]
        return jsonify({
            'user_id': user_id,
            'balance': user['balance'],
            'inventory': user['inventory'],
            'is_new': user['is_new'],
            'is_admin': user_id in ADMIN_IDS
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/update', methods=['POST'])
def update_user():
    """Обновить данные пользователя"""
    try:
        data = request.json
        user_id = data.get('user_id')
        balance = data.get('balance')
        inventory = data.get('inventory')
        is_new = data.get('is_new')
        
        if not user_id:
            return jsonify({'error': 'user_id required'}), 400
        
        if user_id not in user_data:
            user_data[user_id] = get_user_data(user_id)
        
        if balance is not None:
            user_data[user_id]['balance'] = balance
        if inventory is not None:
            user_data[user_id]['inventory'] = inventory
        if is_new is not None:
            user_data[user_id]['is_new'] = is_new
        
        return jsonify({'status': 'updated'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== ПРОМОКОДЫ API =====

@app.route('/api/promo/create', methods=['POST'])
def create_promo():
    """Создать промокод"""
    try:
        data = request.json
        user_id = data.get('user_id')
        
        if user_id not in ADMIN_IDS:
            return jsonify({'error': 'Admin only'}), 403
        
        promo_name = data.get('promo_name')
        reward_type = data.get('reward_type')
        reward_amount = data.get('reward_amount')
        reward_gift = data.get('reward_gift')
        max_activations = data.get('max_activations', 100)
        
        if not promo_name or not reward_type:
            return jsonify({'error': 'Missing fields'}), 400
        
        promo_codes[promo_name] = {
            'type': reward_type,
            'reward_amount': reward_amount,
            'reward_gift': reward_gift,
            'max_activations': max_activations,
            'activations': 0,
            'created_at': datetime.now().isoformat(),
            'used_by': []
        }
        
        return jsonify({
            'status': 'created',
            'promo_name': promo_name,
            'activation_link': f"https://t.me/rps_game_bot?start=promo_{promo_name}"
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/promo/list', methods=['GET'])
def list_promos():
    """Получить список промокодов (только для админа)"""
    try:
        user_id = request.args.get('user_id')
        
        if user_id not in ADMIN_IDS:
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

@app.route('/api/promo/activate', methods=['POST'])
def activate_promo():
    """Активировать промокод"""
    try:
        data = request.json
        user_id = data.get('user_id')
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
        
        if user_id not in user_data:
            user_data[user_id] = get_user_data(user_id)
        
        user = user_data[user_id]
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
        user_id = data.get('user_id')
        promo_name = data.get('promo_name')
        
        if user_id not in ADMIN_IDS:
            return jsonify({'error': 'Admin only'}), 403
        
        if promo_name in promo_codes:
            del promo_codes[promo_name]
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
        
        if str(user_id) not in ADMIN_IDS and int(user_id) not in ADMIN_IDS:
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
        
        if str(user_id) not in ADMIN_IDS and int(user_id) not in ADMIN_IDS:
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
        target_user_id = data.get('user_id')
        new_balance = data.get('balance')
        new_inventory = data.get('inventory')
        
        if admin_id not in ADMIN_IDS and int(admin_id) not in ADMIN_IDS:
            return jsonify({'error': 'Admin only'}), 403
        
        if target_user_id not in user_data:
            user_data[target_user_id] = get_user_data(target_user_id)
        
        user = user_data[target_user_id]
        
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
        
        return jsonify({'status': 'updated'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== АДМИН API - ПОДАРКИ =====

@app.route('/api/admin/gifts', methods=['GET'])
def admin_get_gifts():
    """Получить список подарков"""
    try:
        user_id = request.args.get('user_id')
        
        if str(user_id) not in ADMIN_IDS and int(user_id) not in ADMIN_IDS:
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
        
        if admin_id not in ADMIN_IDS and int(admin_id) not in ADMIN_IDS:
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
        
        if admin_id not in ADMIN_IDS and int(admin_id) not in ADMIN_IDS:
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)