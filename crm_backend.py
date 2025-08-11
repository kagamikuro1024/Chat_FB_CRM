from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
import json
import sqlite3
import os
import logging
from datetime import datetime
import bcrypt
from cryptography.fernet import Fernet
import base64

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Khởi tạo database
def init_database():
    conn = sqlite3.connect('crm_facebook.db')
    cursor = conn.cursor()
    
    # Bảng tài khoản Facebook
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS facebook_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id_chat TEXT UNIQUE NOT NULL,
            username TEXT NOT NULL,
            encrypted_password TEXT NOT NULL,
            two_fa_code TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_online TIMESTAMP
        )
    ''')
    
    # Bảng cuộc hội thoại
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            facebook_account_id INTEGER,
            participant_name TEXT NOT NULL,
            participant_url TEXT NOT NULL,
            conversation_url TEXT NOT NULL,
            unread_count INTEGER DEFAULT 0,
            last_message_timestamp TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (facebook_account_id) REFERENCES facebook_accounts (id)
        )
    ''')
    
    # Bảng tin nhắn
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER,
            sender_name TEXT NOT NULL,
            content TEXT NOT NULL,
            is_from_crm BOOLEAN DEFAULT 0,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_read BOOLEAN DEFAULT 0,
            FOREIGN KEY (conversation_id) REFERENCES conversations (id)
        )
    ''')
    
    # Bảng bài đăng
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            facebook_account_id INTEGER,
            content TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            posted_at TIMESTAMP,
            FOREIGN KEY (facebook_account_id) REFERENCES facebook_accounts (id)
        )
    ''')
    
    # Bảng thông báo
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            facebook_account_id INTEGER,
            content TEXT NOT NULL,
            notification_type TEXT DEFAULT 'notification',
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_read BOOLEAN DEFAULT 0,
            FOREIGN KEY (facebook_account_id) REFERENCES facebook_accounts (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Khởi tạo encryption key
def get_encryption_key():
    key_file = 'encryption.key'
    if not os.path.exists(key_file):
        key = Fernet.generate_key()
        with open(key_file, 'wb') as f:
            f.write(key)
    else:
        with open(key_file, 'rb') as f:
            key = f.read()
    return key

encryption_key = get_encryption_key()
cipher_suite = Fernet(encryption_key)

# Mã hóa và giải mã mật khẩu
def encrypt_password(password):
    return cipher_suite.encrypt(password.encode()).decode()

def decrypt_password(encrypted_password):
    return cipher_suite.decrypt(encrypted_password.encode()).decode()

# Lưu trữ thông tin bot instances
bot_instances = {}

# REST API Endpoints

@app.route('/api/fb_accounts', methods=['GET'])
def get_facebook_accounts():
    """Lấy danh sách tài khoản Facebook và trạng thái"""
    conn = sqlite3.connect('crm_facebook.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, user_id_chat, username, is_active, last_online 
        FROM facebook_accounts
    ''')
    
    accounts = []
    for row in cursor.fetchall():
        account = {
            'id': row[0],
            'user_id_chat': row[1],
            'username': row[2],
            'is_active': bool(row[3]),
            'last_online': row[4],
            'is_online': row[1] in bot_instances
        }
        accounts.append(account)
    
    conn.close()
    return jsonify({'accounts': accounts})

@app.route('/api/fb_accounts', methods=['POST'])
def add_facebook_account():
    """Thêm tài khoản Facebook mới"""
    data = request.json
    user_id_chat = data.get('user_id_chat')
    username = data.get('username')
    password = data.get('password')
    two_fa_code = data.get('two_fa_code')
    
    if not all([user_id_chat, username, password]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    encrypted_password = encrypt_password(password)
    
    conn = sqlite3.connect('crm_facebook.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO facebook_accounts (user_id_chat, username, encrypted_password, two_fa_code)
            VALUES (?, ?, ?, ?)
        ''', (user_id_chat, username, encrypted_password, two_fa_code))
        
        conn.commit()
        account_id = cursor.lastrowid
        
        conn.close()
        return jsonify({'id': account_id, 'message': 'Account added successfully'})
    
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': 'Account already exists'}), 400

@app.route('/api/conversations/<user_id_chat>', methods=['GET'])
def get_conversations(user_id_chat):
    """Lấy danh sách cuộc hội thoại của một tài khoản Facebook"""
    conn = sqlite3.connect('crm_facebook.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT c.id, c.participant_name, c.participant_url, c.conversation_url, 
               c.unread_count, c.last_message_timestamp
        FROM conversations c
        JOIN facebook_accounts fa ON c.facebook_account_id = fa.id
        WHERE fa.user_id_chat = ?
        ORDER BY c.last_message_timestamp DESC
    ''', (user_id_chat,))
    
    conversations = []
    for row in cursor.fetchall():
        conversation = {
            'id': row[0],
            'participant_name': row[1],
            'participant_url': row[2],
            'conversation_url': row[3],
            'unread_count': row[4],
            'last_message_timestamp': row[5]
        }
        conversations.append(conversation)
    
    conn.close()
    return jsonify({'conversations': conversations})

@app.route('/api/messages/<conversation_id>', methods=['GET'])
def get_messages(conversation_id):
    """Lấy tin nhắn trong một cuộc hội thoại"""
    conn = sqlite3.connect('crm_facebook.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, sender_name, content, is_from_crm, timestamp, is_read
        FROM messages
        WHERE conversation_id = ?
        ORDER BY timestamp ASC
    ''', (conversation_id,))
    
    messages = []
    for row in cursor.fetchall():
        message = {
            'id': row[0],
            'sender_name': row[1],
            'content': row[2],
            'is_from_crm': bool(row[3]),
            'timestamp': row[4],
            'is_read': bool(row[5])
        }
        messages.append(message)
    
    # Đánh dấu tin nhắn đã đọc
    cursor.execute('''
        UPDATE messages SET is_read = 1 
        WHERE conversation_id = ? AND is_from_crm = 0
    ''', (conversation_id,))
    
    # Cập nhật unread_count
    cursor.execute('''
        UPDATE conversations SET unread_count = 0 
        WHERE id = ?
    ''', (conversation_id,))
    
    conn.commit()
    conn.close()
    
    return jsonify({'messages': messages})

@app.route('/api/send_message_from_crm', methods=['POST'])
def send_message_from_crm():
    """Gửi tin nhắn từ CRM"""
    data = request.json
    user_id_chat = data.get('user_id_chat')
    participant_url = data.get('participant_url')
    content = data.get('content')
    
    if not all([user_id_chat, participant_url, content]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Lưu tin nhắn vào database
    conn = sqlite3.connect('crm_facebook.db')
    cursor = conn.cursor()
    
    # Tìm conversation_id
    cursor.execute('''
        SELECT c.id FROM conversations c
        JOIN facebook_accounts fa ON c.facebook_account_id = fa.id
        WHERE fa.user_id_chat = ? AND c.participant_url = ?
    ''', (user_id_chat, participant_url))
    
    result = cursor.fetchone()
    if not result:
        conn.close()
        return jsonify({'error': 'Conversation not found'}), 404
    
    conversation_id = result[0]
    
    # Lưu tin nhắn
    cursor.execute('''
        INSERT INTO messages (conversation_id, sender_name, content, is_from_crm)
        VALUES (?, ?, ?, 1)
    ''', (conversation_id, 'CRM User', content))
    
    conn.commit()
    conn.close()
    
    # Gửi lệnh tới bot
    if user_id_chat in bot_instances:
        bot_sid = bot_instances[user_id_chat]
        socketio.emit('send_message_command', {
            'recipient_url': participant_url,
            'message_content': content
        }, room=bot_sid)
        return jsonify({'message': 'Message sent to bot'})
    else:
        return jsonify({'error': 'Bot not online'}), 400

@app.route('/api/post_to_facebook', methods=['POST'])
def post_to_facebook():
    """Đăng bài lên Facebook"""
    data = request.json
    user_id_chat = data.get('user_id_chat')
    content = data.get('content')
    
    if not all([user_id_chat, content]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Lưu bài đăng vào database
    conn = sqlite3.connect('crm_facebook.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id FROM facebook_accounts WHERE user_id_chat = ?
    ''', (user_id_chat,))
    
    result = cursor.fetchone()
    if not result:
        conn.close()
        return jsonify({'error': 'Account not found'}), 404
    
    account_id = result[0]
    
    cursor.execute('''
        INSERT INTO posts (facebook_account_id, content, status)
        VALUES (?, ?, 'pending')
    ''', (account_id, content))
    
    post_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    # Gửi lệnh tới bot
    if user_id_chat in bot_instances:
        bot_sid = bot_instances[user_id_chat]
        socketio.emit('post_news_feed_command', {
            'content': content,
            'post_id': post_id
        }, room=bot_sid)
        return jsonify({'message': 'Post command sent to bot', 'post_id': post_id})
    else:
        return jsonify({'error': 'Bot not online'}), 400

@app.route('/api/notifications/<user_id_chat>', methods=['GET'])
def get_notifications(user_id_chat):
    """Lấy danh sách thông báo của một tài khoản Facebook"""
    conn = sqlite3.connect('crm_facebook.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT n.id, n.content, n.notification_type, n.timestamp, n.is_read
        FROM notifications n
        JOIN facebook_accounts fa ON n.facebook_account_id = fa.id
        WHERE fa.user_id_chat = ?
        ORDER BY n.timestamp DESC
        LIMIT 50
    ''', (user_id_chat,))
    
    notifications = []
    for row in cursor.fetchall():
        notification = {
            'id': row[0],
            'content': row[1],
            'notification_type': row[2],
            'timestamp': row[3],
            'is_read': bool(row[4])
        }
        notifications.append(notification)
    
    conn.close()
    return jsonify({'notifications': notifications})

# Socket.IO Events

@socketio.event
def connect():
    """Bot hoặc Frontend kết nối"""
    logger.info(f"Client connected: {request.sid}")

@socketio.event
def disconnect():
    """Bot hoặc Frontend ngắt kết nối"""
    logger.info(f"Client disconnected: {request.sid}")
    
    # Xóa bot instance nếu là bot
    for user_id_chat, sid in list(bot_instances.items()):
        if sid == request.sid:
            del bot_instances[user_id_chat]
            emit('bot_status_update', {
                'user_id_chat': user_id_chat,
                'status': 'offline'
            }, broadcast=True)
            break

@socketio.event
def bot_register(data):
    """Bot đăng ký với user_id_chat"""
    user_id_chat = data.get('user_id_chat')
    if user_id_chat:
        bot_instances[user_id_chat] = request.sid
        emit('bot_status_update', {
            'user_id_chat': user_id_chat,
            'status': 'online'
        }, broadcast=True)
        logger.info(f"Bot registered: {user_id_chat}")

@socketio.event
def new_messages(data):
    """Nhận tin nhắn mới từ bot"""
    user_id_chat = data.get('user_id_chat')
    messages = data.get('messages', [])
    
    conn = sqlite3.connect('crm_facebook.db')
    cursor = conn.cursor()
    
    for message_data in messages:
        participant_name = message_data.get('participant_name')
        participant_url = message_data.get('participant_url')
        conversation_url = message_data.get('conversation_url')
        content = message_data.get('content')
        sender_name = message_data.get('sender_name', participant_name)
        is_reply = message_data.get('is_reply', False)
        replied_content = message_data.get('replied_content', '')
        replied_to = message_data.get('replied_to', '')
        
        # Tìm hoặc tạo conversation
        cursor.execute('''
            SELECT c.id FROM conversations c
            JOIN facebook_accounts fa ON c.facebook_account_id = fa.id
            WHERE fa.user_id_chat = ? AND c.participant_url = ?
        ''', (user_id_chat, participant_url))
        
        result = cursor.fetchone()
        if result:
            conversation_id = result[0]
        else:
            # Tạo conversation mới
            cursor.execute('''
                SELECT id FROM facebook_accounts WHERE user_id_chat = ?
            ''', (user_id_chat,))
            account_result = cursor.fetchone()
            if account_result:
                account_id = account_result[0]
            else:
                # Tạo tài khoản mới nếu chưa có
                cursor.execute('''
                    INSERT INTO facebook_accounts (user_id_chat, username, encrypted_password)
                    VALUES (?, ?, ?)
                ''', (user_id_chat, f"Account_{user_id_chat}", "dummy_password"))
                account_id = cursor.lastrowid
            
            cursor.execute('''
                INSERT INTO conversations (facebook_account_id, participant_name, participant_url, conversation_url)
                VALUES (?, ?, ?, ?)
            ''', (account_id, participant_name, participant_url, conversation_url))
            conversation_id = cursor.lastrowid
        
        # Lưu tin nhắn
        cursor.execute('''
            INSERT INTO messages (conversation_id, sender_name, content, is_from_crm)
            VALUES (?, ?, ?, 0)
        ''', (conversation_id, sender_name, content))
        
        # Cập nhật unread_count và last_message_timestamp
        cursor.execute('''
            UPDATE conversations 
            SET unread_count = unread_count + 1, last_message_timestamp = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (conversation_id,))
    
    conn.commit()
    conn.close()
    
    # Gửi tin nhắn mới tới Frontend
    emit('crm_new_message', {
        'user_id_chat': user_id_chat,
        'messages': messages
    }, broadcast=True)

@socketio.event
def new_notifications(data):
    """Nhận thông báo mới từ bot"""
    user_id_chat = data.get('user_id_chat')
    notifications = data.get('notifications', [])
    
    conn = sqlite3.connect('crm_facebook.db')
    cursor = conn.cursor()
    
    for notification_data in notifications:
        content = notification_data.get('content')
        notification_type = notification_data.get('type', 'notification')
        timestamp = notification_data.get('timestamp')
        
        # Lưu thông báo vào database
        cursor.execute('''
            INSERT INTO notifications (facebook_account_id, content, notification_type, timestamp)
            VALUES ((SELECT id FROM facebook_accounts WHERE user_id_chat = ?), ?, ?, ?)
        ''', (user_id_chat, content, notification_type, timestamp))
    
    conn.commit()
    conn.close()
    
    # Gửi thông báo mới tới Frontend
    emit('crm_new_notification', {
        'user_id_chat': user_id_chat,
        'notifications': notifications
    }, broadcast=True)

@socketio.event
def post_status_update(data):
    """Cập nhật trạng thái đăng bài"""
    post_id = data.get('post_id')
    status = data.get('status')  # 'success' hoặc 'failed'
    error_message = data.get('error_message', '')
    
    conn = sqlite3.connect('crm_facebook.db')
    cursor = conn.cursor()
    
    if status == 'success':
        cursor.execute('''
            UPDATE posts SET status = 'posted', posted_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (post_id,))
    else:
        cursor.execute('''
            UPDATE posts SET status = 'failed'
            WHERE id = ?
        ''', (post_id,))
    
    conn.commit()
    conn.close()
    
    # Gửi cập nhật tới Frontend
    emit('crm_post_status', {
        'post_id': post_id,
        'status': status,
        'error_message': error_message
    }, broadcast=True)

@socketio.event
def ping(data):
    """Xử lý ping để giữ kết nối"""
    user_id_chat = data.get('user_id_chat', 'unknown')
    print(f"[SOCKET] Ping từ {user_id_chat}")
    emit('pong', {'user_id_chat': user_id_chat})

if __name__ == '__main__':
    init_database()
    socketio.run(app, host='0.0.0.0', port=5000, debug=True) 