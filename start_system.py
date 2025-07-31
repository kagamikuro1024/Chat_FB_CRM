#!/usr/bin/env python3
"""
Script khởi động tự động cho CRM Facebook Management System
"""

import json
import subprocess
import sys
import time
import os
import signal
import threading
from pathlib import Path

class SystemManager:
    def __init__(self):
        self.processes = []
        self.running = True
        
    def load_accounts(self):
        """Tải danh sách tài khoản từ user_accounts.json"""
        try:
            with open('user_accounts.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print("❌ File user_accounts.json không tồn tại!")
            print("📝 Vui lòng tạo file user_accounts.json với cấu trúc:")
            print("""
[
  {
    "user_id_chat": "account1",
    "facebook_username": "your_facebook_username",
    "facebook_password": "your_facebook_password",
    "facebook_2fa_code": "your_2fa_code_if_needed"
  }
]
            """)
            return []
        except json.JSONDecodeError:
            print("❌ File user_accounts.json có lỗi định dạng JSON!")
            return []

    def start_backend(self):
        """Khởi động CRM Backend"""
        print("🚀 Khởi động CRM Backend...")
        try:
            process = subprocess.Popen([
                sys.executable, 'crm_backend.py'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.processes.append(('Backend', process))
            print("✅ CRM Backend đã khởi động")
            return True
        except Exception as e:
            print(f"❌ Lỗi khởi động Backend: {e}")
            return False

    def start_bot(self, account_data):
        """Khởi động một Facebook Bot"""
        user_id_chat = account_data['user_id_chat']
        username = account_data['facebook_username']
        
        print(f"🤖 Khởi động Bot cho tài khoản: {username} ({user_id_chat})")
        
        try:
            process = subprocess.Popen([
                sys.executable, 'toolfacebook.py', user_id_chat
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.processes.append((f'Bot-{user_id_chat}', process))
            print(f"✅ Bot {username} đã khởi động")
            return True
        except Exception as e:
            print(f"❌ Lỗi khởi động Bot {username}: {e}")
            return False

    def start_all_bots(self, accounts):
        """Khởi động tất cả Facebook Bots"""
        print(f"🤖 Khởi động {len(accounts)} Facebook Bot...")
        
        for account in accounts:
            self.start_bot(account)
            time.sleep(2)  # Delay giữa các bot để tránh quá tải

    def monitor_processes(self):
        """Giám sát các process đang chạy"""
        while self.running:
            for name, process in self.processes[:]:
                if process.poll() is not None:
                    print(f"⚠️  Process {name} đã dừng (exit code: {process.returncode})")
                    self.processes.remove((name, process))
                    
                    # Tự động khởi động lại nếu là bot
                    if name.startswith('Bot-'):
                        print(f"🔄 Tự động khởi động lại {name}...")
                        user_id_chat = name.replace('Bot-', '')
                        # Tìm account data và khởi động lại
                        accounts = self.load_accounts()
                        for account in accounts:
                            if account['user_id_chat'] == user_id_chat:
                                self.start_bot(account)
                                break
            
            time.sleep(5)  # Kiểm tra mỗi 5 giây

    def stop_all(self):
        """Dừng tất cả processes"""
        print("🛑 Đang dừng tất cả processes...")
        self.running = False
        
        for name, process in self.processes:
            print(f"🛑 Dừng {name}...")
            try:
                process.terminate()
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                print(f"⚠️  Force kill {name}")
                process.kill()
            except Exception as e:
                print(f"❌ Lỗi khi dừng {name}: {e}")

    def signal_handler(self, signum, frame):
        """Xử lý signal để dừng hệ thống"""
        print("\n🛑 Nhận signal dừng hệ thống...")
        self.stop_all()
        sys.exit(0)

    def run(self):
        """Chạy toàn bộ hệ thống"""
        print("🎯 CRM Facebook Management System")
        print("=" * 50)
        
        # Đăng ký signal handler
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # Tải danh sách tài khoản
        accounts = self.load_accounts()
        if not accounts:
            print("❌ Không có tài khoản nào để khởi động!")
            return
        
        print(f"📋 Tìm thấy {len(accounts)} tài khoản")
        
        # Khởi động Backend
        if not self.start_backend():
            print("❌ Không thể khởi động Backend!")
            return
        
        # Đợi Backend khởi động
        print("⏳ Đợi Backend khởi động...")
        time.sleep(5)
        
        # Khởi động tất cả Bots
        self.start_all_bots(accounts)
        
        print("\n🎉 Hệ thống đã khởi động thành công!")
        print("📱 Mở file crm_frontend.html trong trình duyệt để sử dụng")
        print("🔄 Hệ thống sẽ tự động khởi động lại các bot nếu chúng dừng")
        print("🛑 Nhấn Ctrl+C để dừng hệ thống")
        
        # Bắt đầu monitoring
        try:
            self.monitor_processes()
        except KeyboardInterrupt:
            print("\n🛑 Nhận lệnh dừng từ người dùng...")
            self.stop_all()

def check_dependencies():
    """Kiểm tra các dependencies cần thiết"""
    required_files = [
        'crm_backend.py',
        'toolfacebook.py',
        'crm_frontend.html',
        'requirements.txt'
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print("❌ Thiếu các file sau:")
        for file in missing_files:
            print(f"   - {file}")
        return False
    
    print("✅ Tất cả file cần thiết đã có")
    return True

def install_dependencies():
    """Cài đặt dependencies"""
    print("📦 Kiểm tra và cài đặt dependencies...")
    try:
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'
        ])
        print("✅ Dependencies đã được cài đặt")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Lỗi cài đặt dependencies: {e}")
        return False

def main():
    """Hàm chính"""
    print("🎯 CRM Facebook Management System - Auto Starter")
    print("=" * 60)
    
    # Kiểm tra dependencies
    if not check_dependencies():
        print("❌ Vui lòng đảm bảo tất cả file cần thiết đã có!")
        return
    
    # Cài đặt dependencies
    if not install_dependencies():
        print("❌ Không thể cài đặt dependencies!")
        return
    
    # Khởi động hệ thống
    manager = SystemManager()
    manager.run()

if __name__ == "__main__":
    main() 