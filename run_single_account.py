#!/usr/bin/env python3
"""
Script để chạy test với một tài khoản Facebook đơn lẻ
"""

import subprocess
import time
import sys
import os
import signal
import threading
import requests

class SingleAccountTest:
    def __init__(self, user_id_chat):
        self.user_id_chat = user_id_chat
        self.processes = []
        self.running = True
        
    def start_crm_backend(self):
        """Khởi động CRM Backend"""
        print("[TEST] Khởi động CRM Backend...")
        try:
            process = subprocess.Popen([
                sys.executable, "crm_backend.py"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace")
            self.processes.append(("CRM Backend", process))
            print("[TEST] CRM Backend đã khởi động")
            return True
        except Exception as e:
            print(f"[TEST] Lỗi khởi động CRM Backend: {e}")
            return False
    
    def start_facebook_bot(self):
        """Khởi động Facebook Bot"""
        print(f"[TEST] Khởi động Facebook Bot với user_id_chat: {self.user_id_chat}")
        try:
            process = subprocess.Popen([
                sys.executable, "toolfacebook_split.py", self.user_id_chat
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace")
            self.processes.append(("Facebook Bot", process))
            print("[TEST] Facebook Bot đã khởi động")
            return True
        except Exception as e:
            print(f"[TEST] Lỗi khởi động Facebook Bot: {e}")
            return False
    
    def wait_for_backend_ready(self, timeout=30):
        """Đợi CRM Backend sẵn sàng"""
        print("[TEST] Đợi CRM Backend khởi động hoàn tất...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get('http://localhost:5000/api/fb_accounts', timeout=2)
                if response.status_code == 200:
                    print("[TEST] CRM Backend đã sẵn sàng!")
                    return True
            except requests.exceptions.RequestException:
                pass
            
            time.sleep(1)
        
        print("[TEST] Timeout đợi CRM Backend")
        return False
    
    def open_frontend(self):
        """Mở giao diện frontend"""
        print("[TEST] Mở giao diện CRM Frontend...")
        try:
            import webbrowser
            webbrowser.open('file://' + os.path.abspath('crm_frontend.html'))
            print("[TEST] Đã mở giao diện CRM Frontend")
        except Exception as e:
            print(f"[TEST] Lỗi mở frontend: {e}")
            print("[TEST] Vui lòng mở file crm_frontend.html trong trình duyệt")
    
    def monitor_processes(self):
        """Giám sát các process đang chạy"""
        while self.running:
            for name, process in self.processes[:]:
                if process.poll() is not None:
                    stdout, stderr = process.communicate()
                    print(f"[TEST] Process {name} đã dừng")
                    if stdout:
                        print(f"[TEST] {name} stdout: {stdout}")
                    if stderr:
                        print(f"[TEST] {name} stderr: {stderr}")
                    
                    self.processes.remove((name, process))
                    
                    if name == "CRM Backend":
                        print("[TEST] CRM Backend dừng, dừng toàn bộ hệ thống...")
                        self.running = False
                        break
            
            time.sleep(5)
    
    def stop_all(self):
        """Dừng tất cả processes"""
        print("[TEST] Đang dừng tất cả processes...")
        self.running = False
        
        for name, process in self.processes:
            try:
                print(f"[TEST] Đang dừng {name}...")
                process.terminate()
                process.wait(timeout=5)
                print(f"[TEST] Đã dừng {name}")
            except subprocess.TimeoutExpired:
                print(f"[TEST] Force kill {name}")
                process.kill()
            except Exception as e:
                print(f"[TEST] Lỗi khi dừng {name}: {e}")
    
    def signal_handler(self, signum, frame):
        """Xử lý signal để dừng hệ thống"""
        print("\n[TEST] Nhận signal dừng, đang dừng hệ thống...")
        self.stop_all()
        sys.exit(0)
    
    def run(self):
        """Chạy test với một tài khoản"""
        print("=" * 50)
        print(f"TEST SINGLE ACCOUNT: {self.user_id_chat}")
        print("=" * 50)
        
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        try:
            # Bước 1: Khởi động CRM Backend
            if not self.start_crm_backend():
                print("[TEST] Không thể khởi động CRM Backend. Dừng.")
                return
            
            # Bước 2: Đợi CRM Backend sẵn sàng
            if not self.wait_for_backend_ready():
                print("[TEST] CRM Backend không khởi động được. Dừng.")
                return
            
            # Bước 3: Khởi động Facebook Bot
            if not self.start_facebook_bot():
                print("[TEST] Không thể khởi động Facebook Bot. Dừng.")
                return
            
            # Bước 4: Mở frontend
            time.sleep(3)
            self.open_frontend()
            
            # Bước 5: Bắt đầu giám sát
            print("[TEST] Hệ thống đã khởi động thành công!")
            print("[TEST] Mở http://localhost:5000 để xem CRM Backend")
            print("[TEST] Mở crm_frontend.html để xem giao diện")
            print("[TEST] Nhấn Ctrl+C để dừng hệ thống")
            
            monitor_thread = threading.Thread(target=self.monitor_processes)
            monitor_thread.daemon = True
            monitor_thread.start()
            
            while self.running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n[TEST] Nhận Ctrl+C, đang dừng...")
        except Exception as e:
            print(f"[TEST] Lỗi không xác định: {e}")
        finally:
            self.stop_all()

def main():
    if len(sys.argv) < 2:
        print("Usage: python run_single_account.py <user_id_chat>")
        print("Example: python run_single_account.py 10406031")
        return
    
    user_id_chat = sys.argv[1]
    test = SingleAccountTest(user_id_chat)
    test.run()

if __name__ == "__main__":
    main() 