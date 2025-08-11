#!/usr/bin/env python3
"""
Script test để load dữ liệu từ db_tin_nhan.json và gửi về CRM backend
"""

import json
import socketio
import time
import sys
import threading

def load_messages_from_db(db_file="db_tin_nhan.json"):
    """Load dữ liệu tin nhắn từ file JSON"""
    try:
        with open(db_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"Lỗi khi đọc file {db_file}: {e}")
        return {}

def send_messages_to_crm(messages_data, user_id_chat="test_account"):
    """Gửi tin nhắn về CRM Backend qua Socket.IO"""
    sio = socketio.Client()
    
    @sio.event
    def connect():
        print(f"[TEST] Đã kết nối với CRM Backend")
        # Đăng ký bot
        sio.emit('bot_register', {'user_id_chat': user_id_chat})
        
        # Gửi từng cuộc trò chuyện
        for chat_id, chat_data in messages_data.items():
            print(f"[TEST] Đang gửi cuộc trò chuyện {chat_id}...")
            
            messages_for_crm = []
            for msg in chat_data.get('last_5_messages', []):
                message_data = {
                    'participant_name': chat_data.get('sender', 'Unknown'),
                    'participant_url': f"https://www.facebook.com/messages/t/{chat_id}",
                    'conversation_url': f"https://www.facebook.com/messages/t/{chat_id}",
                    'content': msg.get('content', ''),
                    'sender_name': msg.get('sender', 'Unknown'),
                    'is_reply': 'replied_content' in msg,
                    'replied_content': msg.get('replied_content', ''),
                    'replied_to': msg.get('replied_to', '')
                }
                messages_for_crm.append(message_data)
            
            # Gửi tin nhắn
            sio.emit('new_messages', {
                'user_id_chat': user_id_chat,
                'messages': messages_for_crm
            })
            
            print(f"[TEST] Đã gửi {len(messages_for_crm)} tin nhắn cho cuộc trò chuyện {chat_id}")
            time.sleep(1)  # Delay giữa các cuộc trò chuyện
        
        print("[TEST] Hoàn thành gửi tất cả tin nhắn")
        print("[TEST] Giữ kết nối để duy trì test...")
    
    @sio.event
    def disconnect():
        print("[TEST] Đã ngắt kết nối")
    
    @sio.event
    def connect_error(data):
        print(f"[TEST] Lỗi kết nối: {data}")
    
    def keep_alive():
        """Giữ kết nối alive"""
        while True:
            try:
                if sio.connected:
                    # Gửi ping để giữ kết nối
                    sio.emit('ping', {'user_id_chat': user_id_chat})
                    print("[TEST] Ping để giữ kết nối...")
                time.sleep(30)  # Ping mỗi 30 giây
            except Exception as e:
                print(f"[TEST] Lỗi trong keep_alive: {e}")
                break
    
    try:
        print("[TEST] Đang kết nối tới CRM Backend...")
        sio.connect('http://localhost:5000')
        print("[TEST] Bắt đầu gửi dữ liệu...")
        
        # Bắt đầu thread giữ kết nối
        keep_alive_thread = threading.Thread(target=keep_alive)
        keep_alive_thread.daemon = True
        keep_alive_thread.start()
        
        # Giữ script chạy
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[TEST] Nhận Ctrl+C, đang dừng...")
            sio.disconnect()
            
    except Exception as e:
        print(f"[TEST] Lỗi kết nối CRM Backend: {e}")
        print("[TEST] Thử kết nối lại sau 5 giây...")
        time.sleep(5)
        return False
    
    return True

def main():
    user_id_chat = sys.argv[1] if len(sys.argv) > 1 else "test_account"
    
    print(f"[TEST] Bắt đầu test với user_id_chat: {user_id_chat}")
    
    # Load dữ liệu từ file
    messages_data = load_messages_from_db()
    
    if not messages_data:
        print("[TEST] Không có dữ liệu để gửi")
        return
    
    print(f"[TEST] Tìm thấy {len(messages_data)} cuộc trò chuyện")
    
    # Thử kết nối với retry
    max_retries = 3
    for attempt in range(max_retries):
        print(f"[TEST] Lần thử kết nối {attempt + 1}/{max_retries}")
        if send_messages_to_crm(messages_data, user_id_chat):
            break
        if attempt < max_retries - 1:
            print(f"[TEST] Đợi 10 giây trước khi thử lại...")
            time.sleep(10)
    else:
        print("[TEST] Không thể kết nối sau nhiều lần thử")

if __name__ == "__main__":
    main()
