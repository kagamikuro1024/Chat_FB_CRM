import time
import json
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
import socketio
import threading
import random


class MessengerScraper:
    def __init__(self, cookies_file, headless=False, pin="888888", db_file="db_tin_nhan.json", user_id_chat="default", facebook_username="default", facebook_password="default"):
        self.cookies_file = cookies_file
        self.pin = pin
        self.driver = None
        self.db_file = db_file
        self.logged_chat_ids = set()
        self.chat_history_db = {}
        self.user_id_chat = user_id_chat
        self.facebook_username = facebook_username
        self.facebook_password = facebook_password
        self.setup_driver(headless)
        
        # Khởi tạo Socket.IO client
        self.sio = socketio.Client()
        self.setup_socket_events()
        
    def setup_socket_events(self):
        @self.sio.event
        def connect():
            print(f"[SOCKET] Đã kết nối với CRM Backend")
            # Đăng ký bot với user_id_chat
            self.sio.emit('bot_register', {'user_id_chat': self.user_id_chat})
            
        @self.sio.event
        def disconnect():
            print(f"[SOCKET] Đã ngắt kết nối với CRM Backend")
            
        @self.sio.event
        def send_message_command(data):
            print(f"[SOCKET] Nhận lệnh gửi tin nhắn: {data}")
            # TODO: Implement gửi tin nhắn
            pass
            
        @self.sio.event
        def post_news_feed_command(data):
            print(f"[SOCKET] Nhận lệnh đăng bài: {data}")
            # TODO: Implement đăng bài
            pass

    def connect_to_crm(self):
        """Kết nối tới CRM Backend"""
        try:
            self.sio.connect('http://localhost:5000')
            print(f"[SOCKET] Đã kết nối thành công với CRM Backend")
            return True
        except Exception as e:
            print(f"[SOCKET] Lỗi kết nối CRM Backend: {e}")
            return False

    def send_messages_to_crm(self, chat_id, messages_data):
        """Gửi tin nhắn mới về CRM Backend"""
        try:
            # Chuẩn bị dữ liệu để gửi
            messages_for_crm = []
            for msg in messages_data.get('last_5_messages', []):
                message_data = {
                    'participant_name': messages_data.get('sender', 'Unknown'),
                    'participant_url': f"https://www.facebook.com/messages/t/{chat_id}",
                    'conversation_url': f"https://www.facebook.com/messages/t/{chat_id}",
                    'content': msg.get('content', ''),
                    'sender_name': msg.get('sender', 'Unknown'),
                    'is_reply': 'replied_content' in msg,
                    'replied_content': msg.get('replied_content', ''),
                    'replied_to': msg.get('replied_to', '')
                }
                messages_for_crm.append(message_data)
            
            # Gửi qua Socket.IO
            self.sio.emit('new_messages', {
                'user_id_chat': self.user_id_chat,
                'messages': messages_for_crm
            })
            print(f"[SOCKET] Đã gửi {len(messages_for_crm)} tin nhắn về CRM")
            
        except Exception as e:
            print(f"[SOCKET] Lỗi khi gửi tin nhắn về CRM: {e}")

    def setup_driver(self, headless):
        print("[SETUP] Bắt đầu thiết lập WebDriver...")
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        if headless:
            print("[SETUP] Chế độ headless được bật.")
            chrome_options.add_argument("--headless")
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        print("[SETUP] WebDriver đã được thiết lập thành công.")
    
    def save_page_source(self, filename="messenger_page_source.html"):
        """Lưu mã nguồn HTML của trang hiện tại vào một tệp."""
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            print(f"[DEBUG] Đã lưu mã nguồn trang vào tệp: {filename}")
        except Exception as e:
            print(f"[LỖI] Không thể lưu mã nguồn trang: {e}")

    def save_element_source(self, element, filename="message_element_source.html"):
        """Lưu mã nguồn HTML của một phần tử cụ thể vào một tệp."""
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(element.get_attribute('outerHTML'))
            print(f"[DEBUG] Đã lưu mã nguồn của phần tử tin nhắn vào tệp: {filename}")
        except Exception as e:
            print(f"[LỖI] Không thể lưu mã nguồn của phần tử: {e}")

    def login(self):
        """Đăng nhập Facebook bằng username và password, nhập từ từ giống người thật."""
        print("[LOGIN] Bắt đầu đăng nhập...")
        self.driver.get("https://www.facebook.com")
        time.sleep(3)
        try:
            # Chờ trang đăng nhập tải xong
            email_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "email"))
            )
            password_input = self.driver.find_element(By.ID, "pass")
            login_button = self.driver.find_element(By.NAME, "login")

            # Nhập username từng ký tự với delay ngẫu nhiên
            print("[LOGIN] Đang nhập tên đăng nhập...")
            for char in self.facebook_username:
                email_input.send_keys(char)
                time.sleep(random.uniform(0.05, 0.2))

            # Nhập password từng ký tự với delay ngẫu nhiên
            print("[LOGIN] Đang nhập mật khẩu...")
            for char in self.facebook_password:
                password_input.send_keys(char)
                time.sleep(random.uniform(0.05, 0.2))
            
            # Nhấp vào nút đăng nhập
            print("[LOGIN] Đang click nút đăng nhập...")
            login_button.click()
            
            time.sleep(10) # Chờ trang tải sau khi đăng nhập
            
            # Kiểm tra xem có đăng nhập thành công không
            if "facebook.com/messages" in self.driver.current_url or "facebook.com" in self.driver.current_url:
                print("[LOGIN] Đăng nhập thành công.")
                # Lưu cookies mới vào file
                self.save_cookies()
                return True
            else:
                print("[LOGIN] Đăng nhập thất bại. Vui lòng kiểm tra lại tài khoản và mật khẩu.")
                return False
        except (NoSuchElementException, TimeoutException) as e:
            print(f"[LOGIN] Lỗi khi tìm kiếm phần tử đăng nhập: {e}")
            return False

    def save_cookies(self):
        """Lưu cookies hiện tại của WebDriver vào file."""
        print("[COOKIES] Đang lưu cookies mới vào file...")
        try:
            with open(self.cookies_file, 'w', encoding='utf-8') as f:
                json.dump(self.driver.get_cookies(), f, ensure_ascii=False, indent=4)
            print(f"[COOKIES] Đã lưu cookies thành công vào {self.cookies_file}.")
        except Exception as e:
            print(f"[LỖI] Không thể lưu cookies: {e}")
    def load_cookies(self):
        print("[COOKIES] Đang tải cookies từ file...")
        self.driver.get("https://www.facebook.com")
        time.sleep(3)
        try:
            with open(self.cookies_file, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            
            # Kiểm tra xem cookies có hợp lệ không
            if not cookies:
                print(f"[COOKIES] File cookies {self.cookies_file} trống.")
                return False
                
            for cookie in cookies:
                # Xóa các key không hợp lệ để tránh lỗi
                cookie_data = {
                    'name': cookie['name'],
                    'value': cookie['value'],
                    'domain': cookie.get('domain', '.facebook.com'),
                    'path': cookie.get('path', '/'),
                    'secure': cookie.get('secure', False),
                    'httpOnly': cookie.get('httpOnly', False)
                }
                # Selenium chỉ chấp nhận expires là số
                if 'expiry' in cookie:
                    cookie_data['expiry'] = cookie['expiry']
                
                try:
                    self.driver.add_cookie(cookie_data)
                except Exception as e:
                    # Bỏ qua các cookie có vấn đề
                    print(f"[COOKIES] Lỗi khi thêm cookie {cookie['name']}: {e}")
                    continue
            
            self.driver.refresh()
            print("[COOKIES] Đã làm mới trang để áp dụng cookies.")
            time.sleep(5)
            
            # Kiểm tra lại xem đăng nhập thành công bằng cookies chưa
            if "login.php" in self.driver.current_url:
                print("[COOKIES] Cookies đã hết hạn hoặc không hợp lệ.")
                return False
            
            print("[COOKIES] Tải cookies thành công.")
            return True
            
        except FileNotFoundError:
            print(f"[LỖI] Không tìm thấy file cookies: {self.cookies_file}. Sẽ tiến hành đăng nhập.")
            return False
        except Exception as e:
            print(f"[LỖI] Lỗi khi tải cookies: {e}. Sẽ tiến hành đăng nhập.")
            return False

    def load_db(self):
        try:
            with open(self.db_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    self.chat_history_db = json.loads(content)
                    self.logged_chat_ids = set(self.chat_history_db.keys())
                else:
                    self.chat_history_db = {}
                    self.logged_chat_ids = set()
            print(f"[DB] Đã tải {len(self.logged_chat_ids)} cuộc trò chuyện từ {self.db_file}.")
        except FileNotFoundError:
            print(f"[DB] Không tìm thấy file {self.db_file}. Sẽ tạo file mới khi có dữ liệu.")
            self.chat_history_db = {}
            self.logged_chat_ids = set()
        except Exception as e:
            print(f"[LỖI] Lỗi khi tải DB: {e}. File có thể bị hỏng.")
            self.chat_history_db = {}
            self.logged_chat_ids = set()

    def save_data_to_file(self):
        try:
            with open(self.db_file, 'w', encoding='utf-8') as f:
                json.dump(self.chat_history_db, f, ensure_ascii=False, indent=4)
            print(f"[DB] Đã lưu dữ liệu vào file {self.db_file}.")
        except Exception as e:
            print(f"[LỖI] Không thể lưu dữ liệu vào file {self.db_file}: {e}")

    def go_to_messenger_unread(self):
        print("[MESSENGER] Truy cập Messenger...")
        self.driver.get("https://www.facebook.com/messages")
        time.sleep(8)
        
        if not hasattr(self, 'pin_handled'):
            self.handle_pin_request()
            self.pin_handled = True
        
        print("[MESSENGER] Đang tìm và nhấp vào tab 'Chưa đọc'/'Unread'...")
        div_selectors = [
            "//div[@role='tab' and .//span[contains(text(), 'Chưa đọc')]]",
            "//div[@role='tab' and .//span[contains(text(), 'Unread')]]",
            "//div[contains(@class, 'x1n2onr6') and .//span[contains(text(), 'Chưa đọc')]]",
            "//div[contains(@class, 'x1n2onr6') and .//span[contains(text(), 'Unread')]]",
            "//div[.//span[text()='Chưa đọc']]",
            "//div[.//span[text()='Unread']]"
        ]
        
        found = False
        for selector in div_selectors:
            try:
                divs = self.driver.find_elements(By.XPATH, selector)
                for div in divs:
                    if div.is_displayed() and div.is_enabled():
                        self.driver.execute_script("arguments[0].click();", div)
                        print("[MESSENGER] Đã click vào tab 'Chưa đọc'/'Unread'.")
                        time.sleep(3)
                        found = True
                        break
                if found:
                    break
            except Exception as e:
                print(f"[LỖI] Lỗi khi tìm/click tab 'Chưa đọc'/'Unread' với selector {selector}: {e}")
        
        if not found:
            print("[CẢNH BÁO] Không tìm thấy tab 'Chưa đọc'/'Unread'.")
        return found

    def handle_pin_request(self):
        print("[PIN] Đang kiểm tra yêu cầu nhập mã PIN...")
        try:
            print("[PIN DEBUG] Bắt đầu tìm kiếm hộp thoại mã PIN...")
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//div[@role='dialog']"))
            )
            print("[PIN DEBUG] Đã tìm thấy hộp thoại. Bắt đầu tìm ô nhập mã PIN...")
            pin_input = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//div[@role='dialog']//input[@aria-label='Mã PIN' or @aria-label='PIN']"))
            )
            print("[PIN DEBUG] Đã tìm thấy ô nhập mã PIN. Bắt đầu điền...")
            
            print(f"[PIN] Đang điền mã PIN: {self.pin}...")
            pin_input.send_keys(self.pin)
            
            print("[PIN DEBUG] Đã điền PIN. Chờ 10 giây để tin nhắn tải...")
            time.sleep(10)
            
            print("[PIN] Quá trình xử lý PIN hoàn tất.")
        except TimeoutException:
            print("[PIN DEBUG] Timeout khi tìm kiếm hộp thoại hoặc ô nhập mã PIN. Có thể popup không hiển thị hoặc selector bị sai.")
            print("[PIN] Không tìm thấy cửa sổ nhập mã PIN hoặc đã bỏ qua.")
        except NoSuchElementException:
            print("[PIN DEBUG] Không tìm thấy một trong các phần tử mã PIN bằng XPath.")
            print("[PIN] Không tìm thấy cửa sổ nhập mã PIN hoặc đã bỏ qua.")
        except Exception as e:
            print(f"[LỖI] Lỗi không xác định khi xử lý mã PIN: {e}")

    def scrape_unread_messages(self):
        newly_scraped_count = 0
        try:
            conversations_panel = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[@role='grid']"))
            )
            print("[SCRAPER] Bắt đầu cuộn để tải tất cả tin nhắn chưa đọc...")
            last_height = self.driver.execute_script("return arguments[0].scrollHeight", conversations_panel)
            while True:
                self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", conversations_panel)
                time.sleep(2)
                new_height = self.driver.execute_script("return arguments[0].scrollHeight", conversations_panel)
                if new_height == last_height:
                    print("[SCRAPER] Đã cuộn hết danh sách tin nhắn chưa đọc.")
                    break
                last_height = new_height
                print(f"[SCRAPER] Đã cuộn xuống, chiều cao mới: {new_height}.")
        except (TimeoutException, NoSuchElementException):
            print("[CẢNH BÁO] Không tìm thấy bảng điều khiển cuộc trò chuyện. Có thể không có tin nhắn chưa đọc nào.")
            return newly_scraped_count

        conversation_elements = self.driver.find_elements(By.XPATH, "//div[@role='grid']//div[@role='row']")
        print(f"[SCRAPER] Tìm thấy tổng cộng {len(conversation_elements)} cuộc trò chuyện.")
        
        for idx, conv in enumerate(conversation_elements):
            try:
                conv = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.XPATH, f"(//div[@role='grid']//div[@role='row'])[{idx + 1}]")))
                
                conv_link = conv.find_element(By.TAG_NAME, "a")
                href = conv_link.get_attribute('href')
                
                chat_id_match = re.search(r't/(\d+)', href)
                if not chat_id_match:
                    continue
                chat_id = chat_id_match.group(1)

                if chat_id in self.logged_chat_ids:
                    print(f"[SCRAPER] Bỏ qua cuộc trò chuyện {idx+1} (ID: {chat_id}) vì đã được xử lý trước đó.")
                    continue
                
                sender_span = conv.find_elements(By.XPATH, ".//span[@dir='auto']")[0]
                sender = sender_span.text.strip()
                
                message_text = "Không có tin nhắn cuối"
                time_text = "Không có thời gian"
                
                spans = conv.find_elements(By.XPATH, ".//span[@dir='auto']")
                if len(spans) > 1:
                    last_message_span = spans[-1]
                    message_text_candidate = last_message_span.text.strip()
                    if message_text_candidate and "Tin nhắn và cuộc gọi" not in message_text_candidate and "End-to-end encrypted" not in message_text_candidate:
                        message_text = message_text_candidate
                        
                try:
                    time_abbr = conv.find_element(By.XPATH, ".//abbr")
                    time_text = time_abbr.get_attribute('aria-label')
                except NoSuchElementException:
                    pass
                
                if message_text == "Không có tin nhắn cuối":
                    continue

                print(f"\n[SCRAPER] Đang xử lý cuộc trò chuyện mới (ID: {chat_id}) từ {sender}...")
                print(f"[SCRAPER] Tin nhắn cuối cùng: \"{message_text}\" | Thời gian: {time_text}")

                actions = ActionChains(self.driver)
                actions.move_to_element(conv).perform()
                
                print("[SCRAPER] Đang click vào cuộc trò chuyện...")
                self.driver.execute_script("arguments[0].click();", conv_link)
                time.sleep(3)
                
                chat_history = self.get_last_n_messages(n=5)
                
                self.chat_history_db[chat_id] = {
                    "sender": sender,
                    "last_message": message_text,
                    "last_message_time": time_text,
                    "last_5_messages": chat_history
                }
                self.logged_chat_ids.add(chat_id)
                self.save_data_to_file()
                
                # Gửi tin nhắn về CRM Backend
                self.send_messages_to_crm(chat_id, self.chat_history_db[chat_id])
                
                newly_scraped_count += 1
                
                print(f"[SCRAPER] Đã lấy và lưu 5 tin nhắn gần nhất cho ID: {chat_id}. Đánh dấu đã đọc.")
                
                print("[SCRAPER] Quay lại trang chính của Messenger...")
                self.driver.get("https://www.facebook.com/messages")
                time.sleep(5)
                
                print("[SCRAPER] Tiếp tục xử lý tin nhắn chưa đọc tiếp theo...")
                if not self.go_to_messenger_unread():
                    print("[LỖI] Không thể quay lại tab 'Chưa đọc'. Dừng xử lý các tin nhắn còn lại.")
                    break
            
            except (NoSuchElementException, StaleElementReferenceException) as e:
                print(f"[LỖI] Lỗi khi xử lý cuộc trò chuyện {idx+1}: {e}. Có thể trang đã thay đổi. Bỏ qua và tiếp tục.")
                try:
                    self.driver.get("https://www.facebook.com/messages")
                    time.sleep(5)
                    self.go_to_messenger_unread()
                except Exception as ex:
                    print(f"[LỖI] Không thể quay lại trang Messenger: {ex}")
                    break
                continue
            except Exception as e:
                print(f"[LỖI] Lỗi không xác định khi xử lý cuộc trò chuyện {idx+1}: {e}. Bỏ qua và tiếp tục.")
                break

        return newly_scraped_count

    def get_last_n_messages(self, n):
        history = []
        try:
            print(f"[LỊCH SỬ] Đang lấy {n} tin nhắn gần nhất...")
            chat_container = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[@role='main']"))
            )

            self.save_page_source("chat_page_source.html")

            message_rows = chat_container.find_elements(By.XPATH, "//div[@role='row']")

            if not message_rows:
                print("[LỊCH SỬ DEBUG] Không tìm thấy hàng tin nhắn nào trong cuộc trò chuyện.")
                return history

            print(f"[LỊCH SỬ] Tìm thấy {len(message_rows)} hàng tin nhắn tổng cộng.")

            processed_count = 0
            for idx in range(len(message_rows) - 1, -1, -1):
                if processed_count >= n:
                    break
                    
                row_elem = message_rows[idx]
                
                try:
                    row_text = row_elem.text.strip()
                    print(f"[LỊCH SỬ DEBUG] Xử lý hàng {idx}: '{row_text[:100]}...'")
                    
                    # Bỏ qua tin nhắn hệ thống
                    system_messages = [
                        "New messages and calls are secured with end-to-end encryption",
                        "Only people in this chat can read, listen to, or share them",
                        "Learn more",
                        "Bạn đã đặt biệt danh",
                        "Messages and calls are secured with end-to-end encryption",
                        "end-to-end encrypted",
                        "You set the nickname",
                        "encryption",
                        "The call ended"
                    ]
                    
                    if any(sys_msg in row_text for sys_msg in system_messages) or "[Hình ảnh]" in row_text:
                        print("[LỊCH SỬ DEBUG] Bỏ qua tin nhắn hệ thống hoặc hình ảnh.")
                        continue
                    
                    if not row_text or len(row_text.strip()) == 0 or self._is_timestamp(row_text.strip()):
                        print(f"[LỊCH SỬ DEBUG] Bỏ qua hàng trống hoặc timestamp: '{row_text.strip()}'")
                        continue
                    
                    if row_text.strip() == "Enter":
                        print("[LỊCH SỬ DEBUG] Bỏ qua tin nhắn chỉ có 'Enter'.")
                        continue
                        
                    sender = "Unknown"
                    content = ""
                    
                    # Kiểm tra hình ảnh
                    try:
                        image_elements = row_elem.find_elements(By.XPATH,  
                            ".//img[contains(@alt, 'Open photo') or contains(@alt, 'Gửi kèm ảnh') or contains(@alt, 'Attached image')]")
                        if image_elements:
                            content = "[Hình ảnh]"
                            is_my_msg = self._is_my_message(row_elem)
                            sender = "Tôi" if is_my_msg else self._extract_sender_name(row_elem, row_text)
                            
                            history.append({"sender": sender, "content": content})
                            processed_count += 1
                            print(f"[LỊCH SỬ] Đã thêm hình ảnh #{processed_count}: {sender} - {content}")
                            continue
                    except:
                        pass
                    
                    # Xử lý tin nhắn reply
                    reply_patterns = [
                        "You replied to yourself", "You replied to their note",
                        "You replied to ", " replied to you",
                        " replied to your note", " replied to their note", "đã trả lời bạn",
                        "đã trả lời ghi chú của bạn"
                    ]
                    
                    is_reply = any(pattern in row_text for pattern in reply_patterns)
                    if is_reply:
                        print(f"[LỊCH SỬ DEBUG] Phát hiện reply message: '{row_text[:100]}...'")
                        
                        lines = row_text.split('\n')
                        first_line = lines[0].strip()
                        
                        # Xác định sender thực sự của tin nhắn reply
                        if "You replied" in first_line or "Bạn đã trả lời" in first_line:
                            sender = "Tôi"
                        else:
                            replied_match = re.match(r'^(.+?)\s+(replied to|đã trả lời)', first_line)
                            if replied_match:
                                sender = replied_match.group(1).strip()
                            else:
                                sender = self._extract_sender_name(row_elem, row_text)
                        
                        # Trích xuất nội dung reply và nội dung mới
                        replied_to, replied_content, content = self._extract_reply_content(row_text, sender)
                        
                        if content or replied_content:
                            message = {"sender": sender, "content": content if content else ""}
                            if replied_content:
                                message["replied_content"] = replied_content
                            if replied_to and replied_to != "Unknown":
                                message["replied_to"] = replied_to
                            
                            history.append(message)
                            processed_count += 1
                            print(f"[LỊCH SỬ] Đã thêm reply #{processed_count}: {sender} - Reply: '{replied_content}' - Content: '{content[:50]}...' - Replied_to: '{replied_to}'")
                        continue
                    
                    # Phân tích tin nhắn thông thường
                    is_my_msg = self._is_my_message(row_elem)
                    print(f"[DEBUG] Row {idx}: is_my_message = {is_my_msg}, text = '{row_text[:50]}...'")
                    
                    if is_my_msg:
                        sender = "Tôi"
                        content = self._clean_my_message_content(row_text)
                    else:
                        lines = row_text.split('\n')
                        first_line = lines[0].strip()
                        
                        if self._is_person_name(first_line):
                            sender = first_line
                            content = '\n'.join(lines[1:]) if len(lines) > 1 else ""
                        else:
                            sender = self._extract_sender_name(row_elem, row_text)
                            content = row_text

                    # Làm sạch nội dung tin nhắn
                    content = self._clean_message_content(content)
                    
                    if content and len(content) > 0:
                        if sender == "Unknown":
                            sender = "Người khác"
                        
                        history.append({"sender": sender, "content": content})
                        processed_count += 1
                        print(f"[LỊCH SỬ] Đã thêm tin nhắn #{processed_count}: {sender} - {content[:50]}...")
                    else:
                        print("[LỊCH SỬ DEBUG] Bỏ qua tin nhắn không có nội dung hợp lệ.")
                        
                except Exception as e:
                    print(f"[LỊCH SỬ LỖI] Lỗi khi xử lý hàng tin nhắn {idx}: {e}")
                    continue
            
            history.reverse()
            print(f"[LỊCH SỬ] Hoàn thành. Đã lấy được {len(history)} tin nhắn.")
            
            return history
                
        except (TimeoutException, NoSuchElementException) as e:
            print(f"[CẢNH BÁO] Không thể lấy lịch sử chat của cuộc trò chuyện hiện tại: {e}.")
            return history

    def _is_timestamp(self, text):
        """Kiểm tra xem text có phải timestamp không"""
        import re
        timestamp_patterns = [
            r'^\d{1,2}/\d{1,2}/\d{2,4},\s+\d{1,2}:\d{2}\s+(AM|PM)$',
            r'^\d{1,2}:\d{2}\s+(AM|PM)$', 
            r'^[A-Za-z]{3}\s+\d{1,2},\s+\d{4},\s+\d{1,2}:\d{2}\s+(AM|PM)$',
            r'^\d{1,2}[hwdm]$',
            r'^\d+\s+(hours?|minutes?|days?|weeks?)\s+ago$',
            r'^(Today|Yesterday|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)$',
            r'^Active\s+(now|\d+\s+(minutes?|hours?|days?)\s+ago)$',
            r'^[A-Za-z]{3}\s+\d{1,2}:\d{2}\s+(AM|PM)$',
        ]
        
        return any(re.match(pattern, text.strip()) for pattern in timestamp_patterns)

    def _clean_message_content(self, content):
        """Làm sạch nội dung tin nhắn, loại bỏ các ký tự thừa"""
        if not content:
            return ""
        
        lines = [line.strip() for line in content.split('\n')]
        clean_lines = []
        
        for line in lines:
            if not line or line.lower() == "enter" or self._is_timestamp(line):
                continue
            # Loại bỏ các prefix không cần thiết
            if line.startswith("You sent") or line.startswith("Bạn đã gửi"):
                continue
            clean_lines.append(line)
            
        return '\n'.join(clean_lines).strip()

    def _clean_my_message_content(self, content):
        """Làm sạch nội dung tin nhắn của mình, loại bỏ prefix 'You sent'"""
        if not content:
            return ""
        
        lines = [line.strip() for line in content.split('\n')]
        clean_lines = []
        
        for line in lines:
            if not line or line.lower() == "enter" or self._is_timestamp(line):
                continue
            # Bỏ qua dòng "You sent"
            if line == "You sent" or line == "Bạn đã gửi":
                continue
            clean_lines.append(line)
            
        return '\n'.join(clean_lines).strip()

    def _extract_reply_content(self, raw_text, reply_sender):
        """
        Trích xuất nội dung tin nhắn trả lời, nội dung tin nhắn mới và tên người gửi gốc.
        Trả về: (replied_to, replied_content, new_content)
        """
        replied_content = ""
        new_content = ""
        replied_to = "Unknown"
        
        text = raw_text.strip()

        # Improved regex to handle various reply formats
        reply_pattern = re.compile(
            r'^(?:You replied to yourself|Bạn đã trả lời chính mình)\n' # Match self-reply header
            r'(?:Original message:\n)?(.*?)\n'                         # Match replied content
            r'(.*?)\n?'                                                # Match new content
            r'(?:Enter)?$',                                             # Match optional "Enter" at the end
            re.DOTALL
        )
        match_self_reply = reply_pattern.match(text)

        if match_self_reply:
            replied_to = "Tôi"
            replied_content = self._clean_message_content(match_self_reply.group(1))
            new_content = self._clean_message_content(match_self_reply.group(2))
            return replied_to, replied_content, new_content

        reply_pattern = re.compile(
            r'^(?:You replied to (.+?)|Bạn đã trả lời (.+?))\n'         # Match reply to other person header
            r'(?:Original message:\n)?(.*?)\n'                         # Match replied content
            r'(.*?)\n?'                                                # Match new content
            r'(?:Enter)?$',                                             # Match optional "Enter" at the end
            re.DOTALL
        )
        match_my_reply_to_other = reply_pattern.match(text)
        
        if match_my_reply_to_other:
            replied_to = match_my_reply_to_other.group(1) or match_my_reply_to_other.group(2)
            replied_content = self._clean_message_content(match_my_reply_to_other.group(3))
            new_content = self._clean_message_content(match_my_reply_to_other.group(4))
            return replied_to, replied_content, new_content

        reply_pattern = re.compile(
            r'^(?:(.+?)\s+replied to you|(.+?)\s+đã trả lời bạn)\n'     # Match reply from other person header
            r'(?:Original message:\n)?(.*?)\n'                         # Match replied content
            r'(.*?)\n?'                                                # Match new content
            r'(?:Enter)?$',                                             # Match optional "Enter" at the end
            re.DOTALL
        )
        match_others_reply_to_me = reply_pattern.match(text)

        if match_others_reply_to_me:
            replied_to = "Tôi"
            replied_content = self._clean_message_content(match_others_reply_to_me.group(3))
            new_content = self._clean_message_content(match_others_reply_to_me.group(4))
            return replied_to, replied_content, new_content

        # Fallback logic for any missed cases
        lines = [line.strip() for line in text.split('\n') if line.strip() and not self._is_timestamp(line)]
        
        if len(lines) > 2:
            reply_header = lines[0]
            if "replied to you" in reply_header or "đã trả lời bạn" in reply_header:
                replied_to = "Tôi"
            elif "replied to yourself" in reply_header or "đã trả lời chính mình" in reply_header:
                replied_to = "Tôi"
            else:
                name_match = re.search(r"^(?:You replied to|Bạn đã trả lời)\s+(.+)$", reply_header)
                if name_match:
                    replied_to = name_match.group(1)

            # Assuming the line after "Original message:" is the replied content, and the last line is new content
            replied_content_line_index = -1
            for i, line in enumerate(lines):
                if line.startswith("Original message:"):
                    replied_content_line_index = i + 1
                    break
            
            if replied_content_line_index != -1 and replied_content_line_index < len(lines) - 1:
                replied_content = lines[replied_content_line_index]
                new_content = lines[-1]
            else:
                new_content = lines[-1]
                
        # Clean the final content
        replied_content = self._clean_message_content(replied_content)
        new_content = self._clean_message_content(new_content)
        
        return replied_to, replied_content, new_content


    def _is_my_message(self, row_elem):
        """Kiểm tra xem tin nhắn có phải của mình không"""
        try:
            row_text = row_elem.text.strip()
            if not row_text:
                return False
                
            lines = row_text.split('\n')
            first_line = lines[0].strip()
            
            # Các indicator rõ ràng cho tin nhắn của mình
            my_indicators = [
                "You sent", "Bạn đã gửi", "You replied to", "Bạn đã trả lời"
            ]
            
            if any(indicator in row_text for indicator in my_indicators):
                print(f"[DEBUG] Phát hiện indicator tin nhắn của tôi: {row_text[:50]}...")
                return True
            
            # Nếu dòng đầu tiên là tên người khác thì chắc chắn không phải tin nhắn của mình
            if self._is_person_name(first_line) and first_line.lower() not in ["you", "bạn"]:
                print(f"[DEBUG] Phát hiện tên người khác: '{first_line}' - Không phải tin nhắn của tôi")
                return False
                
            # Kiểm tra CSS styling
            try:
                # Tin nhắn của mình thường có background xanh
                blue_elements = row_elem.find_elements(By.XPATH,
                    ".//div[contains(@style, 'background') and contains(@style, 'rgb(0, 132, 255)')]")
                if blue_elements:
                    print(f"[DEBUG] Phát hiện background xanh - Tin nhắn của tôi")
                    return True
                    
                # Kiểm tra vị trí căn phải (tin nhắn của mình thường căn phải)
                right_aligned = row_elem.find_elements(By.XPATH,
                    ".//div[contains(@class, 'x78zum5') and contains(@class, 'xdt5ytf')]")
                if right_aligned and not self._is_person_name(first_line):
                    print(f"[DEBUG] Căn phải + không có tên người - Tin nhắn của tôi")
                    return True
            except:
                pass
                
            # Mặc định: nếu không có tên người ở đầu và không phải timestamp
            if not self._is_person_name(first_line) and not self._is_timestamp(first_line):
                print(f"[DEBUG] Không có tên người, không phải timestamp - Có thể là tin nhắn của tôi")
                return True
                
            print(f"[DEBUG] Xác định là tin nhắn của người khác: '{first_line}'")
            return False
            
        except Exception as e:
            print(f"[DEBUG] Lỗi _is_my_message: {e}")
            return False

    def _is_person_name(self, text):
        """Kiểm tra xem text có phải là tên người không"""
        import re
        
        if not text:
            return False
        
        # Loại trừ các trường hợp rõ ràng không phải tên
        if self._is_timestamp(text):
            return False
        if text.isdigit():
            return False
        if len(text) > 50:  # Quá dài
            return False
        if text.lower() in ["enter", "you sent", "bạn đã gửi", "you", "bạn"]:
            return False
            
        # Danh sách tên thường gặp
        common_names = ["Trung", "Linh", "Quang Trung", "Diệu Linh", "Quang", "Diệu", "Mi Xơn", "Nguyễn Thu Hiền", "Hiền"]
        if text in common_names:
            return True
            
        # Pattern tên người Việt Nam: 1-4 từ, mỗi từ bắt đầu bằng chữ hoa
        vietnamese_name_pattern = r'^[A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ][a-zàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]*(\s[A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ][a-zàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]*){0,3}$'
        
        if re.match(vietnamese_name_pattern, text):
            return True
            
        return False

    def _extract_sender_name(self, row_elem, row_text):
        """Trích xuất tên người gửi từ các thuộc tính DOM"""
        try:
            # Thử lấy từ aria-label
            aria_label = row_elem.get_attribute("aria-label")
            if aria_label and aria_label.strip():
                # Làm sạch aria-label để lấy tên
                clean_name = aria_label.strip()
                if self._is_person_name(clean_name.split()[0]):  # Lấy từ đầu tiên
                    return clean_name.split()[0]
            
            # Thử tìm element chứa tên người gửi
            name_selectors = [
                ".//span[contains(@class, 'x193iq5w')]",
                ".//div[contains(@class, 'x1n2onr6')]//span",
                ".//strong",
            ]
            
            for selector in name_selectors:
                elements = row_elem.find_elements(By.XPATH, selector)
                for elem in elements:
                    potential_name = elem.text.strip()
                    if self._is_person_name(potential_name):
                        return potential_name
            
            # Thử phân tích từ row_text
            lines = row_text.split('\n')
            first_line = lines[0].strip()
            if self._is_person_name(first_line):
                return first_line
                
            return "Người khác"
            
        except Exception as e:
            print(f"[DEBUG] Lỗi extract_sender_name: {e}")
            return "Người khác"
    def monitor_new_messages(self, interval=30):
        print("[MONITOR] Bắt đầu cào các tin nhắn chưa đọc hiện có...")
        
        # Kết nối tới CRM Backend
        if not self.connect_to_crm():
            print("[MONITOR] Không thể kết nối CRM Backend. Tiếp tục chạy offline.")
        
        if self.go_to_messenger_unread():
            self.scrape_unread_messages()
        else:
             print("[MONITOR] Không thể truy cập tab 'Chưa đọc'. Dừng cào tin nhắn ban đầu.")

        print(f"[MONITOR] Bắt đầu giám sát tin nhắn mới mỗi {interval} giây. Nhấn Ctrl+C để dừng.")
        
        # Lưu trạng thái cuộc trò chuyện để so sánh
        previous_conversations = set()
        conversation_timestamps = {}
        
        try:
            while True:
                time.sleep(interval)
                print(f"\n[MONITOR] Đang quét tin nhắn mới...")
                
                # Lấy danh sách cuộc trò chuyện hiện tại
                current_conversations = self.get_current_conversations()
                
                # So sánh với trạng thái trước
                new_conversations = current_conversations - previous_conversations
                updated_conversations = self.detect_updated_conversations(conversation_timestamps)
                
                if new_conversations or updated_conversations:
                    print(f"[MONITOR] Phát hiện {len(new_conversations)} cuộc trò chuyện mới và {len(updated_conversations)} cuộc trò chuyện cập nhật")
                    
                    # Cào tin nhắn mới
                    self.driver.get("https://www.facebook.com/messages")
                    time.sleep(5)
                    
                    if self.go_to_messenger_unread():
                        newly_scraped_count = self.scrape_unread_messages()
                        if newly_scraped_count > 0:
                            print(f"[MONITOR] Đã cào {newly_scraped_count} cuộc trò chuyện mới")
                        else:
                            print("[MONITOR] Không có tin nhắn mới cần cào")
                    else:
                        print("[MONITOR] Không thể truy cập tab 'Chưa đọc'")
                    
                    # Cập nhật trạng thái
                    previous_conversations = current_conversations
                    conversation_timestamps = self.get_conversation_timestamps()
                else:
                    print("[MONITOR] Không có thay đổi trong cuộc trò chuyện")
                
        except KeyboardInterrupt:
            print("\n[MONITOR] Đã dừng chương trình.")

    def get_current_conversations(self):
        """Lấy danh sách ID cuộc trò chuyện hiện tại"""
        conversations = set()
        try:
            self.driver.get("https://www.facebook.com/messages")
            time.sleep(3)
            
            if not self.go_to_messenger_unread():
                return conversations
            
            conversation_elements = self.driver.find_elements(By.XPATH, "//div[@role='grid']//div[@role='row']")
            
            for conv in conversation_elements:
                try:
                    conv_link = conv.find_element(By.TAG_NAME, "a")
                    href = conv_link.get_attribute('href')
                    
                    chat_id_match = re.search(r't/(\d+)', href)
                    if chat_id_match:
                        chat_id = chat_id_match.group(1)
                        conversations.add(chat_id)
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"[MONITOR] Lỗi khi lấy danh sách cuộc trò chuyện: {e}")
        
        return conversations

    def get_conversation_timestamps(self):
        """Lấy timestamp của các cuộc trò chuyện"""
        timestamps = {}
        try:
            conversation_elements = self.driver.find_elements(By.XPATH, "//div[@role='grid']//div[@role='row']")
            
            for conv in conversation_elements:
                try:
                    conv_link = conv.find_element(By.TAG_NAME, "a")
                    href = conv_link.get_attribute('href')
                    
                    chat_id_match = re.search(r't/(\d+)', href)
                    if chat_id_match:
                        chat_id = chat_id_match.group(1)
                        
                        # Lấy timestamp từ abbr element
                        try:
                            time_abbr = conv.find_element(By.XPATH, ".//abbr")
                            timestamp = time_abbr.get_attribute('aria-label')
                            timestamps[chat_id] = timestamp
                        except NoSuchElementException:
                            timestamps[chat_id] = "unknown"
                            
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"[MONITOR] Lỗi khi lấy timestamp: {e}")
        
        return timestamps

    def detect_updated_conversations(self, previous_timestamps):
        """Phát hiện cuộc trò chuyện có tin nhắn mới"""
        updated = set()
        current_timestamps = self.get_conversation_timestamps()
        
        for chat_id, current_time in current_timestamps.items():
            if chat_id in previous_timestamps:
                previous_time = previous_timestamps[chat_id]
                if current_time != previous_time:
                    updated.add(chat_id)
                    print(f"[MONITOR] Cuộc trò chuyện {chat_id} có tin nhắn mới: {previous_time} -> {current_time}")
        
        return updated

    def close(self):
        print("[CLOSE] Đang đóng WebDriver...")
        if self.driver:
            self.driver.quit()
        print("[CLOSE] WebDriver đã đóng.")

def main():
    import sys
    COOKIES_FILE = "fb_cookies.json"
    PIN = "888888"
    DATABASE_FILE = "db_tin_nhan.json"
    
    # Lấy user_id_chat từ command line argument
    user_id_chat = sys.argv[1] if len(sys.argv) > 1 else "default"
    facebook_username = "0386122204"
    facebook_password = "Trung5kvshth@"

    
    scraper = MessengerScraper(
        cookies_file=COOKIES_FILE, 
        pin=PIN, 
        headless=False, 
        db_file=DATABASE_FILE,
        user_id_chat=user_id_chat,
        facebook_username=facebook_username,
        facebook_password=facebook_password,
    )
    try:
        # Thử tải cookies
        if not scraper.load_cookies():
            # Nếu không thành công, thử đăng nhập bằng tài khoản/mật khẩu
            if not scraper.login():
                print("[CHƯƠNG TRÌNH] Đăng nhập thất bại. Dừng chương trình.")
                return
            
        # Nếu đã có cookies hoặc đăng nhập thành công, tiếp tục chạy
        scraper.load_db()
        scraper.monitor_new_messages(interval=30)
    finally:
        scraper.close()

if __name__ == "__main__":
    main()