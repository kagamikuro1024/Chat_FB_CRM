#!/usr/bin/env python3
"""
Facebook Bot với kiến trúc API tách biệt
Kết nối với cả Receiver API và Sender API
"""

import asyncio
import json
import logging
import os
import random
import sys
import time
from datetime import datetime
from pathlib import Path

import requests
import socketio
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Cấu hình API endpoints
RECEIVER_API_URL = "http://localhost:5001"
SENDER_API_URL = "http://localhost:5002"

class FacebookBotSplit:
    def __init__(self, user_id_chat, username, password, two_fa_code=""):
        self.user_id_chat = user_id_chat
        self.username = username
        self.password = password
        self.two_fa_code = two_fa_code
        self.browser = None
        self.wait = None
        self.is_running = False
        
        # Socket.IO clients
        self.receiver_socket = socketio.AsyncClient()
        self.sender_socket = socketio.AsyncClient()
        
        # Đăng ký event handlers
        self._register_socket_events()

    def _register_socket_events(self):
        """Đăng ký các event handlers cho Socket.IO"""
        
        @self.receiver_socket.event
        async def connect():
            logger.info(f"Bot {self.username} đã kết nối với Receiver API")
            await self.receiver_socket.emit('bot_register', {
                'user_id_chat': self.user_id_chat,
                'username': self.username
            })
        
        @self.sender_socket.event
        async def connect():
            logger.info(f"Bot {self.username} đã kết nối với Sender API")
            await self.sender_socket.emit('bot_register', {
                'user_id_chat': self.user_id_chat,
                'username': self.username
            })
        
        @self.sender_socket.on('send_message_command')
        async def on_send_message_command(data):
            """Nhận lệnh gửi tin nhắn từ CRM"""
            recipient_url = data.get('recipient_url')
            message_content = data.get('message_content')
            
            if recipient_url and message_content:
                try:
                    await self.send_message(recipient_url, message_content)
                    logger.info(f"Đã gửi tin nhắn: {message_content[:50]}...")
                except Exception as e:
                    logger.error(f"Lỗi khi gửi tin nhắn: {e}")
        
        @self.sender_socket.on('post_news_feed_command')
        async def on_post_news_feed_command(data):
            """Nhận lệnh đăng bài từ CRM"""
            content = data.get('content')
            post_id = data.get('post_id')
            
            if content:
                try:
                    await self._post_news_feed(content, post_id)
                    logger.info(f"Đã đăng bài: {content[:50]}...")
                except Exception as e:
                    logger.error(f"Lỗi khi đăng bài: {e}")
                    await self._send_post_status_to_crm(post_id, 'failed', str(e))

    async def _init_browser(self):
        """Khởi tạo browser"""
        try:
            options = webdriver.ChromeOptions()
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            self.browser = webdriver.Chrome(options=options)
            self.browser.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.wait = WebDriverWait(self.browser, 10)
            
            logger.info("Browser đã được khởi tạo")
            return True
        except Exception as e:
            logger.error(f"Lỗi khởi tạo browser: {e}")
            return False

    async def login(self):
        """Đăng nhập Facebook"""
        try:
            logger.info(f"Đang đăng nhập tài khoản {self.username}...")
            self.browser.get("https://www.facebook.com/")
            await asyncio.sleep(2)
            
            # Nhập username
            username_field = self.wait.until(EC.presence_of_element_located((By.ID, "email")))
            username_field.clear()
            username_field.send_keys(self.username)
            
            # Nhập password
            password_field = self.browser.find_element(By.ID, "pass")
            password_field.clear()
            password_field.send_keys(self.password)
            
            # Click đăng nhập
            login_button = self.browser.find_element(By.NAME, "login")
            login_button.click()
            
            await asyncio.sleep(3)
            
            # Xử lý 2FA nếu có
            if self.two_fa_code:
                try:
                    code_field = self.wait.until(EC.presence_of_element_located((By.NAME, "approvals_code")))
                    code_field.send_keys(self.two_fa_code)
                    
                    continue_button = self.browser.find_element(By.ID, "checkpointSubmitButton")
                    continue_button.click()
                    await asyncio.sleep(3)
                except:
                    logger.warning("Không tìm thấy trường 2FA")
            
            # Kiểm tra đăng nhập thành công
            if "facebook.com" in self.browser.current_url and "login" not in self.browser.current_url:
                logger.info(f"Đăng nhập thành công: {self.username}")
                return True
            else:
                logger.error("Đăng nhập thất bại")
                return False
                
        except Exception as e:
            logger.error(f"Lỗi đăng nhập: {e}")
            return False

    async def scrape_new_messages(self):
        """Cào tin nhắn mới từ Facebook"""
        try:
            logger.info(f"Đang cào tin nhắn mới cho {self.username}...")
            self.browser.get("https://www.facebook.com/messages/")
            await asyncio.sleep(3)
            
            new_messages = []
            
            # Tìm các cuộc hội thoại có tin nhắn mới
            conversation_elements = self.browser.find_elements(By.XPATH, 
                "//div[@role='row' and contains(@class, 'x1n2onr6')] | " +
                "//div[contains(@class, 'x1n2onr6') and contains(@class, 'x1ja2u2z')]"
            )
            
            for conv_elem in conversation_elements[:5]:  # Chỉ xử lý 5 cuộc hội thoại đầu
                try:
                    # Lấy thông tin người gửi
                    sender_elem = conv_elem.find_element(By.XPATH, 
                        ".//span[contains(@class, 'x1lliihq')] | " +
                        ".//div[contains(@class, 'x1n2onr6')]//span"
                    )
                    sender_name = sender_elem.text if sender_elem else "Unknown"
                    
                    # Lấy URL cuộc hội thoại
                    conversation_url = conv_elem.get_attribute("href") or ""
                    
                    # Lấy tin nhắn cuối
                    message_elem = conv_elem.find_element(By.XPATH,
                        ".//div[contains(@class, 'x1n2onr6')]//span[last()] | " +
                        ".//span[contains(@class, 'x1lliihq')][last()]"
                    )
                    last_message = message_elem.text if message_elem else ""
                    
                    if last_message and sender_name != "Unknown":
                        new_messages.append({
                            "participant_name": sender_name,
                            "participant_url": conversation_url,
                            "conversation_url": conversation_url,
                            "content": last_message
                        })
                        
                except Exception as e:
                    continue
            
            if new_messages:
                logger.info(f"Tìm thấy {len(new_messages)} tin nhắn mới cho {self.username}")
                await self._send_messages_to_receiver(new_messages)
            
            return new_messages
            
        except Exception as e:
            logger.error(f"Lỗi trong scrape_new_messages cho {self.username}: {e}")
            return []

    async def scrape_notifications(self):
        """Cào thông báo mới từ Facebook"""
        try:
            logger.info(f"Đang cào thông báo mới cho {self.username}...")
            self.browser.get("https://www.facebook.com/notifications/")
            await asyncio.sleep(3)
            
            notifications = []
            notification_elements = self.browser.find_elements(By.XPATH, 
                "//div[@role='article' and contains(@class, 'x1n2onr6')] | " +
                "//div[contains(@aria-label, 'notification')] | " +
                "//div[contains(@class, 'x1n2onr6') and contains(@class, 'x1ja2u2z')]"
            )
            
            for notif_elem in notification_elements[:10]:
                try:
                    content_elem = notif_elem.find_element(By.XPATH, 
                        ".//span[contains(@class, 'x1lliihq')] | " +
                        ".//div[contains(@class, 'x1n2onr6')]//span"
                    )
                    notification_text = content_elem.text if content_elem else ""
                    
                    if notification_text:
                        notifications.append({
                            "type": "notification",
                            "content": notification_text,
                            "timestamp": time.time()
                        })
                        
                except Exception as e:
                    continue
            
            if notifications:
                logger.info(f"Tìm thấy {len(notifications)} thông báo mới cho {self.username}")
                await self._send_notifications_to_receiver(notifications)
            
            return notifications
            
        except Exception as e:
            logger.error(f"Lỗi trong scrape_notifications cho {self.username}: {e}")
            return []

    async def send_message(self, recipient_url, message_content):
        """Gửi tin nhắn đến người dùng"""
        try:
            # Mở cuộc hội thoại
            self.browser.get(recipient_url)
            await asyncio.sleep(2)
            
            # Tìm ô nhập tin nhắn
            message_input = self.wait.until(EC.presence_of_element_located((
                By.XPATH, "//div[@contenteditable='true' and @role='textbox'] | " +
                         "//textarea[@placeholder*='message' or @placeholder*='tin nhắn']"
            )))
            
            # Nhập tin nhắn
            message_input.clear()
            message_input.send_keys(message_content)
            await asyncio.sleep(1)
            
            # Gửi tin nhắn
            message_input.send_keys(Keys.RETURN)
            await asyncio.sleep(2)
            
            logger.info(f"Đã gửi tin nhắn: {message_content[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"Lỗi khi gửi tin nhắn: {e}")
            return False

    async def _post_news_feed(self, content, post_id=None):
        """Đăng bài lên Facebook"""
        try:
            logger.info(f"Đang đăng bài cho {self.username}...")
            self.browser.get("https://www.facebook.com/")
            await asyncio.sleep(3)
            
            # Tìm ô nhập bài viết
            post_input = self.wait.until(EC.presence_of_element_located((
                By.XPATH, "//div[@contenteditable='true' and @data-testid='posting_message_input'] | " +
                         "//div[@contenteditable='true' and contains(@aria-label, 'post')]"
            )))
            
            # Nhập nội dung
            post_input.clear()
            post_input.send_keys(content)
            await asyncio.sleep(1)
            
            # Tìm nút đăng bài
            post_button = self.browser.find_element(By.XPATH,
                "//div[@data-testid='posting_submit_button'] | " +
                "//button[contains(text(), 'Post') or contains(text(), 'Đăng')]"
            )
            
            # Đăng bài
            post_button.click()
            await asyncio.sleep(3)
            
            logger.info(f"Đã đăng bài thành công: {content[:50]}...")
            
            if post_id:
                await self._send_post_status_to_crm(post_id, 'success')
            
            return True
            
        except Exception as e:
            logger.error(f"Lỗi khi đăng bài: {e}")
            if post_id:
                await self._send_post_status_to_crm(post_id, 'failed', str(e))
            return False

    async def _send_messages_to_receiver(self, messages):
        """Gửi tin nhắn mới đến Receiver API"""
        try:
            # Gửi qua REST API
            response = requests.post(f"{RECEIVER_API_URL}/api/bot/new_messages", json={
                'user_id_chat': self.user_id_chat,
                'messages': messages
            })
            
            if response.status_code == 200:
                logger.info(f"Đã gửi {len(messages)} tin nhắn đến Receiver API")
            else:
                logger.error(f"Lỗi gửi tin nhắn đến Receiver API: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Lỗi khi gửi tin nhắn đến Receiver API: {e}")

    async def _send_notifications_to_receiver(self, notifications):
        """Gửi thông báo mới đến Receiver API"""
        try:
            # Gửi qua REST API
            response = requests.post(f"{RECEIVER_API_URL}/api/bot/new_notifications", json={
                'user_id_chat': self.user_id_chat,
                'notifications': notifications
            })
            
            if response.status_code == 200:
                logger.info(f"Đã gửi {len(notifications)} thông báo đến Receiver API")
            else:
                logger.error(f"Lỗi gửi thông báo đến Receiver API: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Lỗi khi gửi thông báo đến Receiver API: {e}")

    async def _send_post_status_to_crm(self, post_id, status, error_message=""):
        """Gửi trạng thái đăng bài đến Sender API"""
        try:
            await self.sender_socket.emit('post_status_update', {
                'post_id': post_id,
                'status': status,
                'error_message': error_message
            })
            logger.info(f"Đã gửi trạng thái đăng bài: {status}")
        except Exception as e:
            logger.error(f"Lỗi khi gửi trạng thái đăng bài: {e}")

    async def run_bot_tasks(self):
        """Chạy các tác vụ định kỳ của bot"""
        while self.is_running:
            try:
                # Cào tin nhắn mới
                await self.scrape_new_messages()
                await asyncio.sleep(random.uniform(3, 5))
                
                # Cào thông báo mới
                await self.scrape_notifications()
                await asyncio.sleep(random.uniform(3, 5))
                
                # Cập nhật trạng thái online
                requests.post(f"{RECEIVER_API_URL}/api/bot/status_update", json={
                    'user_id_chat': self.user_id_chat,
                    'status': 'online'
                })
                
                await asyncio.sleep(random.uniform(10, 15))
                
            except Exception as e:
                logger.error(f"Lỗi trong run_bot_tasks: {e}")
                await asyncio.sleep(30)

    async def start(self):
        """Khởi động bot"""
        try:
            logger.info(f"🚀 Khởi động Facebook Bot cho {self.username}")
            
            # Khởi tạo browser
            if not await self._init_browser():
                return False
            
            # Đăng nhập
            if not await self.login():
                return False
            
            # Kết nối Socket.IO
            await self.receiver_socket.connect(RECEIVER_API_URL)
            await self.sender_socket.connect(SENDER_API_URL)
            
            self.is_running = True
            
            # Chạy các tác vụ
            await self.run_bot_tasks()
            
        except Exception as e:
            logger.error(f"Lỗi khi khởi động bot: {e}")
            return False

    async def stop(self):
        """Dừng bot"""
        self.is_running = False
        
        # Thông báo offline
        try:
            requests.post(f"{RECEIVER_API_URL}/api/bot/status_update", json={
                'user_id_chat': self.user_id_chat,
                'status': 'offline'
            })
        except:
            pass
        
        # Đóng browser
        if self.browser:
            self.browser.quit()
        
        # Đóng Socket.IO
        await self.receiver_socket.disconnect()
        await self.sender_socket.disconnect()
        
        logger.info(f"Bot {self.username} đã dừng")

async def run_facebook_bot_split(account_data):
    """Chạy Facebook Bot với kiến trúc tách biệt"""
    bot = FacebookBotSplit(
        user_id_chat=account_data['user_id_chat'],
        username=account_data['facebook_username'],
        password=account_data['facebook_password'],
        two_fa_code=account_data.get('facebook_2fa_code', '')
    )
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        logger.info("Nhận lệnh dừng từ người dùng")
    except Exception as e:
        logger.error(f"Lỗi khi chạy bot: {e}")
    finally:
        await bot.stop()

def load_account_by_user_id(user_id_chat):
    """Tải thông tin tài khoản từ user_accounts.json"""
    try:
        with open('user_accounts.json', 'r', encoding='utf-8') as f:
            accounts = json.load(f)
        
        for account in accounts:
            if account['user_id_chat'] == user_id_chat:
                return account
        return None
    except Exception as e:
        logger.error(f"Lỗi khi tải thông tin tài khoản: {e}")
        return None

def main():
    """Hàm chính"""
    if len(sys.argv) != 2:
        print("Cách sử dụng: python toolfacebook_split.py <user_id_chat>")
        print("Ví dụ: python toolfacebook_split.py account1")
        return
    
    user_id_chat = sys.argv[1]
    account_data = load_account_by_user_id(user_id_chat)
    
    if not account_data:
        print(f"❌ Không tìm thấy tài khoản với user_id_chat: {user_id_chat}")
        return
    
    print(f"🎯 Khởi động bot cho tài khoản: {account_data.get('note', 'Unknown')}")
    print(f"📧 Username: {account_data['facebook_username']}")
    print(f"🆔 User ID: {account_data['user_id_chat']}")
    print("=" * 50)
    
    try:
        asyncio.run(run_facebook_bot_split(account_data))
    except KeyboardInterrupt:
        print("\n🛑 Bot đã được dừng bởi người dùng")
    except Exception as e:
        print(f"❌ Lỗi khi chạy bot: {e}")

if __name__ == "__main__":
    main() 