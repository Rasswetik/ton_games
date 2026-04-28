"""
SQLite Database для Multiplayer Rooms и Games
"""
import sqlite3
import json
from pathlib import Path
from datetime import datetime
from enum import Enum

DB_PATH = Path('data/multiplayer.db')

class GameStatus(Enum):
    WAITING = 'waiting'
    COUNTDOWN = 'countdown'
    PLAYING = 'playing'
    FINISHED = 'finished'

def init_database():
    """Инициализировать базу данных"""
    DB_PATH.parent.mkdir(exist_ok=True)
    
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # Таблица комнат
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS rooms (
        room_id TEXT PRIMARY KEY,
        stake REAL NOT NULL,
        min_players INTEGER NOT NULL,
        max_players INTEGER NOT NULL,
        rounds INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'waiting',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        started_at TIMESTAMP,
        finished_at TIMESTAMP,
        winner_id TEXT,
        pool REAL DEFAULT 0
    )
    ''')
    
    # Таблица игроков в комнате
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS room_players (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_id TEXT NOT NULL,
        user_id TEXT NOT NULL,
        username TEXT,
        avatar_url TEXT,
        balance_before REAL,
        current_round_choice TEXT,
        rounds_won INTEGER DEFAULT 0,
        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(room_id) REFERENCES rooms(room_id),
        UNIQUE(room_id, user_id)
    )
    ''')
    
    # Таблица раундов
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS game_rounds (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_id TEXT NOT NULL,
        round_number INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'playing',
        round_data TEXT,
        winner_id TEXT,
        completed_at TIMESTAMP,
        FOREIGN KEY(room_id) REFERENCES rooms(room_id)
    )
    ''')
    
    # Таблица ходов в раунде
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS round_moves (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        round_id INTEGER NOT NULL,
        user_id TEXT NOT NULL,
        choice TEXT,
        made_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(round_id) REFERENCES game_rounds(id)
    )
    ''')
    
    conn.commit()
    conn.close()
    print("[✅] Multiplayer database initialized")

def create_room(room_id, stake, min_players, max_players, rounds):
    """Создать новую комнату"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
        INSERT INTO rooms (room_id, stake, min_players, max_players, rounds, status)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (room_id, stake, min_players, max_players, rounds, 'waiting'))
        
        # ===== IMPORTANT: Create initial game round for round 1 =====
        cursor.execute('''
        INSERT INTO game_rounds (room_id, round_number, status)
        VALUES (?, ?, ?)
        ''', (room_id, 1, 'playing'))
        
        conn.commit()
        print(f"[✅] Room created: {room_id}, Round 1 initialized")
        return True
    except Exception as e:
        print(f"[❌] Error creating room: {e}")
        return False
    finally:
        conn.close()

def get_rooms(status='waiting'):
    """Получить комнаты по статусу"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
        SELECT r.*, COUNT(rp.user_id) as players_count
        FROM rooms r
        LEFT JOIN room_players rp ON r.room_id = rp.room_id
        WHERE r.status = ?
        GROUP BY r.room_id
        ''', (status,))
        
        rows = cursor.fetchall()
        rooms = []
        
        for row in rows:
            rooms.append({
                'room_id': row[0],
                'stake': row[1],
                'min_players': row[2],
                'max_players': row[3],
                'rounds': row[4],
                'status': row[5],
                'created_at': row[6],
                'started_at': row[7],
                'finished_at': row[8],
                'winner_id': row[9],
                'pool': row[10],
                'players_count': row[11]
            })
        
        return rooms
    except Exception as e:
        print(f"[❌] Error getting rooms: {e}")
        return []
    finally:
        conn.close()

def get_room(room_id):
    """Получить информацию о комнате"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
        SELECT r.*, COUNT(rp.user_id) as players_count
        FROM rooms r
        LEFT JOIN room_players rp ON r.room_id = rp.room_id
        WHERE r.room_id = ?
        GROUP BY r.room_id
        ''', (room_id,))
        
        row = cursor.fetchone()
        
        if row:
            room_dict = {
                'room_id': row[0],
                'stake': row[1],
                'min_players': row[2],
                'max_players': row[3],
                'rounds': row[4],
                'status': row[5],
                'created_at': row[6],
                'started_at': row[7],
                'finished_at': row[8],
                'winner_id': row[9],
                'pool': row[10],
                'players_count': row[11],
                'current_round': 1  # Default to round 1
            }
            
            # Get current round from game_rounds if it exists
            try:
                cursor.execute('''
                SELECT MAX(round_number) FROM game_rounds
                WHERE room_id = ?
                ''', (room_id,))
                current_round = cursor.fetchone()[0]
                if current_round:
                    room_dict['current_round'] = current_round
            except:
                pass
            
            return room_dict
        return None
    except Exception as e:
        print(f"[❌] Error getting room: {e}")
        return None
    finally:
        conn.close()

def join_room(room_id, user_id, username, avatar_url, balance):
    """Присоединиться к комнате (или вернуться, если уже был)"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        # Проверить, уже ли в комнате
        cursor.execute('''
        SELECT id FROM room_players WHERE room_id = ? AND user_id = ?
        ''', (room_id, user_id))
        
        existing = cursor.fetchone()
        if existing:
            print(f"[✅] Player {user_id} re-joined room {room_id} (already in room)")
            conn.close()
            return True
        
        # Попытаться добавить нового игрока
        cursor.execute('''
        INSERT INTO room_players (room_id, user_id, username, avatar_url, balance_before)
        VALUES (?, ?, ?, ?, ?)
        ''', (room_id, user_id, username, avatar_url, balance))
        
        conn.commit()
        print(f"[✅] Player {user_id} joined room {room_id}")
        return True
    except Exception as e:
        print(f"[❌] Error joining room: {e}")
        return False
    finally:
        conn.close()

def get_room_players(room_id):
    """Получить всех игроков в комнате"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
        SELECT user_id, username, avatar_url, balance_before, rounds_won
        FROM room_players
        WHERE room_id = ?
        ''', (room_id,))
        
        rows = cursor.fetchall()
        players = []
        
        for row in rows:
            players.append({
                'user_id': row[0],
                'username': row[1],
                'avatar_url': row[2],
                'balance_before': row[3],
                'rounds_won': row[4]
            })
        
        return players
    except Exception as e:
        print(f"[❌] Error getting room players: {e}")
        return []
    finally:
        conn.close()

def make_move(room_id, user_id, choice, round_number):
    """Сделать ход в раунде (камень, ножницы, бумага)"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        # Сначала получить round_id текущего раунда
        cursor.execute('''
        SELECT id FROM game_rounds
        WHERE room_id = ? AND round_number = ?
        ''', (room_id, round_number))
        
        round_row = cursor.fetchone()
        
        # If round doesn't exist, create it (shouldn't happen with fix, but safety measure)
        if not round_row:
            print(f"[⚠️] Round {round_number} doesn't exist for room {room_id}, creating it...")
            cursor.execute('''
            INSERT INTO game_rounds (room_id, round_number, status)
            VALUES (?, ?, ?)
            ''', (room_id, round_number, 'playing'))
            conn.commit()
            
            cursor.execute('''
            SELECT id FROM game_rounds
            WHERE room_id = ? AND round_number = ?
            ''', (room_id, round_number))
            round_row = cursor.fetchone()
        
        if not round_row:
            print(f"[❌] Failed to create or find round {round_number} for room {room_id}")
            return False
        
        round_id = round_row[0]
        
        # Обновить выбор игрока
        cursor.execute('''
        UPDATE room_players
        SET current_round_choice = ?
        WHERE room_id = ? AND user_id = ?
        ''', (choice, room_id, user_id))
        
        # Записать ход
        cursor.execute('''
        INSERT INTO round_moves (round_id, user_id, choice)
        VALUES (?, ?, ?)
        ''', (round_id, user_id, choice))
        
        conn.commit()
        print(f"[✅] Move recorded: user {user_id} played {choice} in round {round_number} of room {room_id}")
        return True
    except Exception as e:
        print(f"[❌] Error making move: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        conn.close()

def update_room_status(room_id, status):
    """Обновить статус комнаты"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
        UPDATE rooms SET status = ? WHERE room_id = ?
        ''', (status, room_id))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"[❌] Error updating room: {e}")
        return False
    finally:
        conn.close()

def cleanup_empty_rooms(timeout_seconds=60):
    """Удалить пустые комнаты (ожидание, < 2 игроков, старше timeout_seconds)"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        # Получить комнаты для удаления
        cursor.execute(f'''
        SELECT r.room_id, COUNT(rp.user_id) as players_count
        FROM rooms r
        LEFT JOIN room_players rp ON r.room_id = rp.room_id
        WHERE r.status = 'waiting' 
        AND datetime(r.created_at) < datetime('now', '-{timeout_seconds} seconds')
        GROUP BY r.room_id
        HAVING players_count < 2
        ''')
        
        rooms_to_delete = cursor.fetchall()
        deleted_count = 0
        
        for room_id, players_count in rooms_to_delete:
            # Вернуть ставки игроков в комнате
            cursor.execute('''
            SELECT user_id, balance_before FROM room_players
            WHERE room_id = ?
            ''', (room_id,))
            
            players = cursor.fetchall()
            
            # Удалить комнату и всех игроков
            cursor.execute('DELETE FROM room_players WHERE room_id = ?', (room_id,))
            cursor.execute('DELETE FROM rooms WHERE room_id = ?', (room_id,))
            
            deleted_count += 1
            print(f"[🗑️] Deleted empty room {room_id} ({players_count} players)")
        
        conn.commit()
        
        if deleted_count > 0:
            print(f"[✅] Cleaned up {deleted_count} empty rooms")
        
        return deleted_count
    except Exception as e:
        print(f"[❌] Error cleaning rooms: {e}")
        import traceback
        traceback.print_exc()
        return 0
    finally:
        conn.close()

# Инициализировать при импорте
try:
    init_database()
    print("[✅] Multiplayer database initialized")
except Exception as e:
    print(f"[WARNING] Database init error: {e}")
