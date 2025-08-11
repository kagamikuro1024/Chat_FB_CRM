#!/usr/bin/env python3
"""
Script khởi động để test toàn bộ hệ thống CRM Facebook
"""

import subprocess
import time
import sys
import os
import signal
import threading
import requests
import json

class CRMTestSystem:
    def __init__(self):
        self.processes = []
        self.running = True
        
    def start_crm_backend(self):
        """Khởi động CRM Backend"""
        print("[SYSTEM] Khởi động CRM Backend...")
        try:
            process = subprocess.Popen([
                sys.executable, "crm_backend.py"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace")
            self.processes.append(("CRM Backend", process))
            print("[SYSTEM] CRM Backend đã khởi động")
            return True
        except Exception as e:
            print(f"[SYSTEM] Lỗi khởi động CRM Backend: {e}")
            return False
    
    def start_api_receiver(self):
        """Khởi động API Receiver"""
        print("[SYSTEM] Khởi động API Receiver...")
        try:
            process = subprocess.Popen([
                sys.executable, "api_receiver.py"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace")
            self.processes.append(("API Receiver", process))
            print("[SYSTEM] API Receiver đã khởi động")
            return True
        except Exception as e:
            print(f"[SYSTEM] Lỗi khởi động API Receiver: {e}")
            return False
    
    def start_facebook_bot(self, user_id_chat="test_account"):
        """Khởi động Facebook Bot"""
        print(f"[SYSTEM] Khởi động Facebook Bot với user_id_chat: {user_id_chat}")
        try:
            process = subprocess.Popen([
                sys.executable, "toolfacebook_split.py", user_id_chat
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace")
            self.processes.append((f"Facebook Bot ({user_id_chat})", process))
            print(f"[SYSTEM] Facebook Bot ({user_id_chat}) đã khởi động")
            return True
        except Exception as e:
            print(f"[SYSTEM] Lỗi khởi động Facebook Bot: {e}")
            return False
    
    def test_with_existing_data(self, user_id_chat="test_account"):
        """Test với dữ liệu có sẵn từ db_tin_nhan.json"""
        print("[SYSTEM] Bắt đầu test với dữ liệu có sẵn...")
        time.sleep(3)  # Đợi CRM Backend khởi động
        
        try:
            process = subprocess.Popen([
                sys.executable, "test_load_messages.py", user_id_chat
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace")
            self.processes.append(("Test Load Messages", process))
            print("[SYSTEM] Đã khởi động test load messages")
            return True
        except Exception as e:
            print(f"[SYSTEM] Lỗi khởi động test: {e}")
            return False
    
    def start_multiple_bots(self):
        """Khởi động nhiều bot với các tài khoản khác nhau"""
        print("[SYSTEM] Khởi động nhiều bot...")
        
        # Load danh sách tài khoản từ user_accounts.json
        try:
            with open('user_accounts.json', 'r', encoding='utf-8') as f:
                accounts = json.load(f)
            
            started_bots = 0
            for account in accounts[:3]:  # Chỉ test 3 tài khoản đầu
                user_id_chat = account['user_id_chat']
                username = account['facebook_username']
                
                print(f"[SYSTEM] Khởi động bot cho tài khoản: {username} ({user_id_chat})")
                if self.start_facebook_bot(user_id_chat):
                    started_bots += 1
                    time.sleep(5)  # Delay giữa các bot
                else:
                    print(f"[SYSTEM] Không thể khởi động bot cho {username}")
            
            print(f"[SYSTEM] Đã khởi động {started_bots} bot thành công")
            return started_bots > 0
            
        except Exception as e:
            print(f"[SYSTEM] Lỗi khi load tài khoản: {e}")
            return False
    
    def wait_for_backend_ready(self, timeout=30):
        """Đợi CRM Backend sẵn sàng"""
        print("[SYSTEM] Đợi CRM Backend khởi động hoàn tất...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get('http://localhost:5000/api/fb_accounts', timeout=2)
                if response.status_code == 200:
                    print("[SYSTEM] CRM Backend đã sẵn sàng!")
                    return True
            except requests.exceptions.RequestException:
                pass
            
            time.sleep(1)
        
        print("[SYSTEM] Timeout đợi CRM Backend")
        return False
    
    def wait_for_receiver_ready(self, timeout=30):
        """Đợi API Receiver sẵn sàng"""
        print("[SYSTEM] Đợi API Receiver khởi động hoàn tất...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get('http://localhost:5001/api/bot/register', timeout=2)
                if response.status_code == 405:  # Method not allowed - server đang chạy
                    print("[SYSTEM] API Receiver đã sẵn sàng!")
                    return True
            except requests.exceptions.RequestException:
                pass
            
            time.sleep(1)
        
        print("[SYSTEM] Timeout đợi API Receiver")
        return False
    
    def open_frontend(self):
        """Mở giao diện frontend"""
        print("[SYSTEM] Mở giao diện CRM Frontend...")
        try:
            # Mở file HTML trong trình duyệt mặc định
            import webbrowser
            webbrowser.open('file://' + os.path.abspath('crm_frontend.html'))
            print("[SYSTEM] Đã mở giao diện CRM Frontend")
        except Exception as e:
            print(f"[SYSTEM] Lỗi mở frontend: {e}")
            print("[SYSTEM] Vui lòng mở file crm_frontend.html trong trình duyệt")
    
    def monitor_processes(self):
        """Giám sát các process đang chạy"""
        while self.running:
            for name, process in self.processes[:]:  # Copy list để tránh lỗi khi modify
                if process.poll() is not None:
                    # Process đã dừng
                    stdout, stderr = process.communicate()
                    print(f"[SYSTEM] Process {name} đã dừng")
                    if stdout:
                        print(f"[SYSTEM] {name} stdout: {stdout}")
                    if stderr:
                        print(f"[SYSTEM] {name} stderr: {stderr}")
                    
                    # Xóa process khỏi list
                    self.processes.remove((name, process))
                    
                    # Nếu là CRM Backend dừng, dừng toàn bộ hệ thống
                    if name == "CRM Backend":
                        print("[SYSTEM] CRM Backend dừng, dừng toàn bộ hệ thống...")
                        self.running = False
                        break
            
            time.sleep(5)
    
    def stop_all(self):
        """Dừng tất cả processes"""
        print("[SYSTEM] Đang dừng tất cả processes...")
        self.running = False
        
        for name, process in self.processes:
            try:
                print(f"[SYSTEM] Đang dừng {name}...")
                process.terminate()
                process.wait(timeout=5)
                print(f"[SYSTEM] Đã dừng {name}")
            except subprocess.TimeoutExpired:
                print(f"[SYSTEM] Force kill {name}")
                process.kill()
            except Exception as e:
                print(f"[SYSTEM] Lỗi khi dừng {name}: {e}")
    
    def signal_handler(self, signum, frame):
        """Xử lý signal để dừng hệ thống"""
        print("\n[SYSTEM] Nhận signal dừng, đang dừng hệ thống...")
        self.stop_all()
        sys.exit(0)
    
    def run(self, test_mode="single"):
        """Chạy toàn bộ hệ thống test"""
        print("=" * 60)
        print("CRM FACEBOOK MANAGEMENT SYSTEM - TEST MODE")
        print(f"Test Mode: {test_mode}")
        print("=" * 60)
        
        # Đăng ký signal handler
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        try:
            # Bước 1: Khởi động CRM Backend
            if not self.start_crm_backend():
                print("[SYSTEM] Không thể khởi động CRM Backend. Dừng.")
                return
            
            # Bước 2: Khởi động API Receiver
            if not self.start_api_receiver():
                print("[SYSTEM] Không thể khởi động API Receiver. Dừng.")
                return
            
            # Bước 3: Đợi các service sẵn sàng
            if not self.wait_for_backend_ready():
                print("[SYSTEM] CRM Backend không khởi động được. Dừng.")
                return
            
            if not self.wait_for_receiver_ready():
                print("[SYSTEM] API Receiver không khởi động được. Dừng.")
                return
            
            # Bước 4: Khởi động bot(s)
            if test_mode == "multiple":
                if not self.start_multiple_bots():
                    print("[SYSTEM] Không thể khởi động bot. Dừng.")
                    return
            else:
                # Test với dữ liệu có sẵn
                if not self.test_with_existing_data():
                    print("[SYSTEM] Không thể chạy test. Dừng.")
                    return
            
            # Bước 5: Mở frontend
            time.sleep(2)
            self.open_frontend()
            
            # Bước 6: Bắt đầu giám sát
            print("[SYSTEM] Hệ thống đã khởi động thành công!")
            print("[SYSTEM] Mở http://localhost:5000 để xem CRM Backend")
            print("[SYSTEM] Mở http://localhost:5001 để xem API Receiver")
            print("[SYSTEM] Mở crm_frontend.html để xem giao diện")
            print("[SYSTEM] Nhấn Ctrl+C để dừng hệ thống")
            
            # Chạy giám sát trong thread riêng
            monitor_thread = threading.Thread(target=self.monitor_processes)
            monitor_thread.daemon = True
            monitor_thread.start()
            
            # Chờ cho đến khi có signal dừng
            while self.running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n[SYSTEM] Nhận Ctrl+C, đang dừng...")
        except Exception as e:
            print(f"[SYSTEM] Lỗi không xác định: {e}")
        finally:
            self.stop_all()

def check_dependencies():
    """Kiểm tra dependencies"""
    required_files = [
        "crm_backend.py",
        "api_receiver.py",
        "toolfacebook_split.py", 
        "test_load_messages.py",
        "crm_frontend.html",
        "db_tin_nhan.json",
        "user_accounts.json"
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"[ERROR] Thiếu các file: {missing_files}")
        return False
    
    print("[SYSTEM] Tất cả file cần thiết đã có")
    return True

def install_dependencies():
    """Cài đặt dependencies"""
    print("[SYSTEM] Kiểm tra và cài đặt dependencies...")
    try:
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "flask", "flask-socketio", "flask-cors", "requests", "python-socketio"])
        print("[SYSTEM] Dependencies đã được cài đặt")
        return True
    except Exception as e:
        print(f"[SYSTEM] Lỗi cài đặt dependencies: {e}")
        return False

def main():
    """Hàm main"""
    if not check_dependencies():
        print("[ERROR] Vui lòng kiểm tra các file cần thiết")
        return
    
    # Kiểm tra argument
    test_mode = "single"
    if len(sys.argv) > 1:
        if sys.argv[1] == "multiple":
            test_mode = "multiple"
        elif sys.argv[1] == "single":
            test_mode = "single"
        else:
            print("Usage: python test_system.py [single|multiple]")
            print("  single: Test với dữ liệu có sẵn")
            print("  multiple: Test với nhiều bot thật")
            return
    
    system = CRMTestSystem()
    system.run(test_mode)

if __name__ == "__main__":
    main()
