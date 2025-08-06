#!/usr/bin/env python3
"""
Script để xóa cookies Facebook
"""

import os
import json
import sys

def clear_facebook_cookies(user_id_chat=None):
    """Xóa file cookies Facebook"""
    if user_id_chat:
        cookies_file = f"fb_cookies_{user_id_chat}.json"
    else:
        cookies_file = "fb_cookies.json"
    
    if os.path.exists(cookies_file):
        try:
            os.remove(cookies_file)
            print(f"✅ Đã xóa file cookies: {cookies_file}")
            print("💡 Lần chạy tiếp theo sẽ đăng nhập bằng username/password")
        except Exception as e:
            print(f"❌ Lỗi khi xóa cookies: {e}")
    else:
        print(f"📋 Không tìm thấy file cookies: {cookies_file}")

def list_cookies_files():
    """Liệt kê tất cả file cookies"""
    import glob
    cookie_files = glob.glob("fb_cookies*.json")
    if cookie_files:
        print("📋 Danh sách file cookies:")
        for file in cookie_files:
            print(f"  - {file}")
    else:
        print("📋 Không có file cookies nào")

if __name__ == "__main__":
    print("🗑️ Xóa cookies Facebook")
    print("=" * 30)
    
    if len(sys.argv) > 1:
        user_id_chat = sys.argv[1]
        print(f"🎯 Xóa cookies cho user_id_chat: {user_id_chat}")
        clear_facebook_cookies(user_id_chat)
    else:
        print("📋 Hiển thị danh sách file cookies:")
        list_cookies_files()
        print("\n💡 Sử dụng: python clear_cookies.py <user_id_chat>")
        print("💡 Ví dụ: python clear_cookies.py account1") 