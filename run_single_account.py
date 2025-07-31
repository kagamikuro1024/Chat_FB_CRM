#!/usr/bin/env python3
"""
Script chạy một tài khoản Facebook riêng lẻ với khả năng đọc thông báo và quản lý tin nhắn
"""

import json
import sys
import asyncio
import os
from toolfacebook import run_facebook_bot_and_socketio

def load_account_by_user_id(user_id_chat):
    """Tải thông tin tài khoản theo user_id_chat"""
    try:
        with open('user_accounts.json', 'r', encoding='utf-8') as f:
            accounts = json.load(f)
        
        for account in accounts:
            if account.get('user_id_chat') == user_id_chat:
                return account
        
        return None
    except FileNotFoundError:
        print("❌ File user_accounts.json không tồn tại!")
        return None
    except json.JSONDecodeError:
        print("❌ File user_accounts.json có lỗi định dạng JSON!")
        return None

def main():
    if len(sys.argv) != 2:
        print("📝 Cách sử dụng:")
        print("python run_single_account.py <user_id_chat>")
        print("\n📋 Danh sách tài khoản có sẵn:")
        
        try:
            with open('user_accounts.json', 'r', encoding='utf-8') as f:
                accounts = json.load(f)
            
            for account in accounts:
                print(f"  - {account['user_id_chat']}: {account['note']} ({account['facebook_username']})")
        except:
            print("  Không thể đọc file user_accounts.json")
        
        return
    
    user_id_chat = sys.argv[1]
    
    # Tải thông tin tài khoản
    account_data = load_account_by_user_id(user_id_chat)
    if not account_data:
        print(f"❌ Không tìm thấy tài khoản với user_id_chat: {user_id_chat}")
        return
    
    print(f"🎯 Khởi động bot cho tài khoản: {account_data['note']}")
    print(f"📧 Username: {account_data['facebook_username']}")
    print(f"🆔 User ID: {account_data['user_id_chat']}")
    print("=" * 50)
    
    # Thiết lập biến môi trường cho bot
    os.environ['USER_ID_CHAT'] = user_id_chat
    
    try:
        # Chạy bot
        asyncio.run(run_facebook_bot_and_socketio(account_data))
    except KeyboardInterrupt:
        print("\n🛑 Bot đã được dừng bởi người dùng")
    except Exception as e:
        print(f"❌ Lỗi khi chạy bot: {e}")

if __name__ == "__main__":
    main() 