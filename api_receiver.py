#!/usr/bin/env python3
"""
API Server để nhận tin nhắn và thông báo từ Facebook Bot
Chạy độc lập với CRM Frontend API
"""

from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import sqlite3
import os
import logging
from datetime import datetime
import json

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'receiver-secret-key'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", port=5001)

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

# Lưu trữ thông tin bot instances
bot_instances = {}

# REST API Endpoints cho việc nhận dữ liệu

@app.route('/api/bot/register', methods=['POST'])
def register_bot():
    """Bot đăng ký với hệ thống"""
    data = request.json
    user_id_chat = data.get('user_id_chat')
    username = data.get('username')
    
    if not user_id_chat or not username:
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Lưu hoặc cập nhật thông tin bot
    conn = sqlite3.connect('crm_facebook.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO facebook_accounts (user_id_chat, username, last_online)
        VALUES (?, ?, CURRENT_TIMESTAMP)
    ''', (user_id_chat, username))
    
    conn.commit()
    conn.close()
    
    # Thông báo cho CRM Frontend
    socketio.emit('bot_status_update', {
        'user_id_chat': user_id_chat,
        'status': 'online',
        'username': username
    }, broadcast=True)
    
    return jsonify({'message': 'Bot registered successfully'})

@app.route('/api/bot/new_messages', methods=['POST'])
def receive_new_messages():
    """Nhận tin nhắn mới từ Facebook Bot"""
    data = request.json
    user_id_chat = data.get('user_id_chat')
    messages = data.get('messages', [])
    
    if not user_id_chat or not messages:
        return jsonify({'error': 'Missing required fields'}), 400
    
    conn = sqlite3.connect('crm_facebook.db')
    cursor = conn.cursor()
    
    processed_messages = []
    
    for message_data in messages:
        participant_name = message_data.get('participant_name')
        participant_url = message_data.get('participant_url')
        conversation_url = message_data.get('conversation_url')
        content = message_data.get('content')
        
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
            account_id = cursor.fetchone()[0]
            
            cursor.execute('''
                INSERT INTO conversations (facebook_account_id, participant_name, participant_url, conversation_url)
                VALUES (?, ?, ?, ?)
            ''', (account_id, participant_name, participant_url, conversation_url))
            conversation_id = cursor.lastrowid
        
        # Lưu tin nhắn
        cursor.execute('''
            INSERT INTO messages (conversation_id, sender_name, content, is_from_crm)
            VALUES (?, ?, ?, 0)
        ''', (conversation_id, participant_name, content))
        
        message_id = cursor.lastrowid
        
        # Cập nhật unread_count và last_message_timestamp
        cursor.execute('''
            UPDATE conversations 
            SET unread_count = unread_count + 1, last_message_timestamp = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (conversation_id,))
        
        processed_messages.append({
            'id': message_id,
            'participant_name': participant_name,
            'participant_url': participant_url,
            'conversation_url': conversation_url,
            'content': content,
            'timestamp': datetime.now().isoformat()
        })
    
    conn.commit()
    conn.close()
    
    # Thông báo cho CRM Frontend
    socketio.emit('crm_new_message', {
        'user_id_chat': user_id_chat,
        'messages': processed_messages
    }, broadcast=True)
    
    return jsonify({'message': f'Processed {len(processed_messages)} messages'})

@app.route('/api/bot/new_notifications', methods=['POST'])
def receive_new_notifications():
    """Nhận thông báo mới từ Facebook Bot"""
    data = request.json
    user_id_chat = data.get('user_id_chat')
    notifications = data.get('notifications', [])
    
    if not user_id_chat or not notifications:
        return jsonify({'error': 'Missing required fields'}), 400
    
    conn = sqlite3.connect('crm_facebook.db')
    cursor = conn.cursor()
    
    processed_notifications = []
    
    for notification_data in notifications:
        content = notification_data.get('content')
        notification_type = notification_data.get('type', 'notification')
        timestamp = notification_data.get('timestamp', datetime.now().isoformat())
        
        # Lưu thông báo vào database
        cursor.execute('''
            INSERT INTO notifications (facebook_account_id, content, notification_type, timestamp)
            VALUES ((SELECT id FROM facebook_accounts WHERE user_id_chat = ?), ?, ?, ?)
        ''', (user_id_chat, content, notification_type, timestamp))
        
        notification_id = cursor.lastrowid
        processed_notifications.append({
            'id': notification_id,
            'content': content,
            'notification_type': notification_type,
            'timestamp': timestamp
        })
    
    conn.commit()
    conn.close()
    
    # Thông báo cho CRM Frontend
    socketio.emit('crm_new_notification', {
        'user_id_chat': user_id_chat,
        'notifications': processed_notifications
    }, broadcast=True)
    
    return jsonify({'message': f'Processed {len(processed_notifications)} notifications'})

@app.route('/api/bot/status_update', methods=['POST'])
def update_bot_status():
    """Cập nhật trạng thái bot"""
    data = request.json
    user_id_chat = data.get('user_id_chat')
    status = data.get('status')  # 'online' hoặc 'offline'
    
    if not user_id_chat or not status:
        return jsonify({'error': 'Missing required fields'}), 400
    
    conn = sqlite3.connect('crm_facebook.db')
    cursor = conn.cursor()
    
    if status == 'online':
        cursor.execute('''
            UPDATE facebook_accounts SET last_online = CURRENT_TIMESTAMP
            WHERE user_id_chat = ?
        ''', (user_id_chat,))
    else:
        cursor.execute('''
            UPDATE facebook_accounts SET last_online = NULL
            WHERE user_id_chat = ?
        ''', (user_id_chat,))
    
    conn.commit()
    conn.close()
    
    # Thông báo cho CRM Frontend
    socketio.emit('bot_status_update', {
        'user_id_chat': user_id_chat,
        'status': status
    }, broadcast=True)
    
    return jsonify({'message': f'Bot status updated to {status}'})

# Socket.IO Events

@socketio.event
def connect():
    """Client kết nối"""
    logger.info(f"Client connected: {request.sid}")

@socketio.event
def disconnect():
    """Client ngắt kết nối"""
    logger.info(f"Client disconnected: {request.sid}")

@socketio.event
def bot_register(data):
    """Bot đăng ký qua Socket.IO"""
    user_id_chat = data.get('user_id_chat')
    username = data.get('username')
    
    if user_id_chat and username:
        bot_instances[user_id_chat] = request.sid
        socketio.emit('bot_status_update', {
            'user_id_chat': user_id_chat,
            'status': 'online',
            'username': username
        }, broadcast=True)
        logger.info(f"Bot registered via Socket.IO: {user_id_chat}")

@socketio.event
def new_messages(data):
    """Nhận tin nhắn mới từ bot qua Socket.IO"""
    user_id_chat = data.get('user_id_chat')
    messages = data.get('messages', [])
    
    # Xử lý tương tự như API endpoint
    conn = sqlite3.connect('crm_facebook.db')
    cursor = conn.cursor()
    
    for message_data in messages:
        participant_name = message_data.get('participant_name')
        participant_url = message_data.get('participant_url')
        conversation_url = message_data.get('conversation_url')
        content = message_data.get('content')
        
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
            cursor.execute('''
                SELECT id FROM facebook_accounts WHERE user_id_chat = ?
            ''', (user_id_chat,))
            account_id = cursor.fetchone()[0]
            
            cursor.execute('''
                INSERT INTO conversations (facebook_account_id, participant_name, participant_url, conversation_url)
                VALUES (?, ?, ?, ?)
            ''', (account_id, participant_name, participant_url, conversation_url))
            conversation_id = cursor.lastrowid
        
        # Lưu tin nhắn
        cursor.execute('''
            INSERT INTO messages (conversation_id, sender_name, content, is_from_crm)
            VALUES (?, ?, ?, 0)
        ''', (conversation_id, participant_name, content))
        
        # Cập nhật unread_count
        cursor.execute('''
            UPDATE conversations 
            SET unread_count = unread_count + 1, last_message_timestamp = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (conversation_id,))
    
    conn.commit()
    conn.close()
    
    # Gửi tin nhắn mới tới Frontend
    socketio.emit('crm_new_message', {
        'user_id_chat': user_id_chat,
        'messages': messages
    }, broadcast=True)

@socketio.event
def new_notifications(data):
    """Nhận thông báo mới từ bot qua Socket.IO"""
    user_id_chat = data.get('user_id_chat')
    notifications = data.get('notifications', [])
    
    conn = sqlite3.connect('crm_facebook.db')
    cursor = conn.cursor()
    
    for notification_data in notifications:
        content = notification_data.get('content')
        notification_type = notification_data.get('type', 'notification')
        timestamp = notification_data.get('timestamp')
        
        cursor.execute('''
            INSERT INTO notifications (facebook_account_id, content, notification_type, timestamp)
            VALUES ((SELECT id FROM facebook_accounts WHERE user_id_chat = ?), ?, ?, ?)
        ''', (user_id_chat, content, notification_type, timestamp))
    
    conn.commit()
    conn.close()
    
    # Gửi thông báo mới tới Frontend
    socketio.emit('crm_new_notification', {
        'user_id_chat': user_id_chat,
        'notifications': notifications
    }, broadcast=True)

if __name__ == '__main__':
    init_database()
    print("🚀 API Receiver Server đang khởi động...")
    print("📍 Port: 5001")
    print("📡 Chức năng: Nhận tin nhắn và thông báo từ Facebook Bot")
    socketio.run(app, host='0.0.0.0', port=5001, debug=True) 