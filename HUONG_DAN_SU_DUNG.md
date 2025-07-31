# Hướng dẫn sử dụng CRM Facebook Management System

## 🎯 Tổng quan

Hệ thống CRM Facebook Management đã được cải thiện với khả năng:
- ✅ **Đọc tin nhắn mới** từ Facebook Messenger
- ✅ **Đọc thông báo mới** từ Facebook
- ✅ **Gửi tin nhắn trả lời** thông qua giao diện CRM
- ✅ **Quản lý nhiều tài khoản** Facebook cùng lúc
- ✅ **Theo dõi real-time** trạng thái online/offline
- ✅ **Đăng bài viết** từ CRM

## 🚀 Cách chạy hệ thống

### 1. Chạy toàn bộ hệ thống (nhiều tài khoản)

```bash
python start_system.py
```

Hệ thống sẽ:
- Khởi động CRM Backend
- Khởi động tất cả Facebook Bots
- Tự động khởi động lại nếu bot bị lỗi

### 2. Chạy một tài khoản riêng lẻ

```bash
# Xem danh sách tài khoản
python run_single_account.py

# Chạy bot cho tài khoản cụ thể
python run_single_account.py 10406031
```

### 3. Chạy từng thành phần riêng biệt

```bash
# Terminal 1: Khởi động CRM Backend
python crm_backend.py

# Terminal 2: Khởi động Facebook Bot cho tài khoản cụ thể
python toolfacebook.py 10406031

# Terminal 3: Mở giao diện web
# Mở file crm_frontend.html trong trình duyệt
```

## 📱 Sử dụng giao diện web

### 1. Truy cập giao diện
- Mở file `crm_frontend.html` trong trình duyệt
- Hoặc chạy HTTP server: `python -m http.server 8000`

### 2. Quản lý tin nhắn
1. **Chọn tài khoản** từ danh sách bên trái
2. **Xem cuộc hội thoại** trong tab "Tin nhắn"
3. **Click vào cuộc hội thoại** để xem tin nhắn
4. **Gửi tin nhắn trả lời** bằng cách nhập và nhấn "Gửi"

### 3. Xem thông báo
1. **Chọn tài khoản** từ danh sách bên trái
2. **Chuyển sang tab "Thông báo"**
3. **Xem danh sách thông báo** mới nhất
4. **Thông báo chưa đọc** sẽ hiển thị đậm hơn

### 4. Đăng bài viết
1. **Chuyển sang tab "Đăng bài"**
2. **Chọn tài khoản** để đăng bài
3. **Nhập nội dung** bài viết
4. **Nhấn "Đăng bài"** - Bot sẽ tự động đăng lên Facebook

## 🔧 Cấu hình tài khoản

### File `user_accounts.json`
```json
[
  {
    "user_id_chat": "10406031",
    "facebook_username": "gianvu17607@gmail.com",
    "facebook_password": "lvqh1234",
    "facebook_2fa_code": "",
    "note": "Chị Dung"
  }
]
```

### Thêm tài khoản mới
1. Thêm thông tin vào `user_accounts.json`
2. Khởi động lại hệ thống hoặc chạy bot riêng lẻ

## 📊 Tính năng chính

### 1. Đọc tin nhắn tự động
- Bot tự động cào tin nhắn mới mỗi 3-5 phút
- Hiển thị real-time trong giao diện CRM
- Lưu trữ lịch sử tin nhắn trong database

### 2. Đọc thông báo tự động
- Bot tự động cào thông báo mới từ Facebook
- Hiển thị trong tab "Thông báo"
- Phân biệt thông báo đã đọc/chưa đọc

### 3. Gửi tin nhắn từ CRM
- Chọn cuộc hội thoại
- Nhập tin nhắn và gửi
- Bot tự động gửi tin nhắn đến Facebook

### 4. Đăng bài viết
- Viết nội dung trong CRM
- Bot tự động đăng lên Facebook
- Theo dõi trạng thái đăng bài

## 🔍 Troubleshooting

### Bot không kết nối được
```bash
# Kiểm tra CRM Backend có đang chạy không
curl http://localhost:5000/api/fb_accounts

# Kiểm tra thông tin tài khoản
cat user_accounts.json
```

### Tin nhắn không hiển thị
1. Kiểm tra bot có online không
2. Kiểm tra XPath selectors có phù hợp không
3. Cập nhật selectors trong `toolfacebook.py`

### Thông báo không cập nhật
1. Kiểm tra kết nối Socket.IO
2. Refresh trang web
3. Kiểm tra console browser

### Lỗi đăng nhập Facebook
1. Kiểm tra username/password
2. Kiểm tra 2FA code nếu có
3. Thử đăng nhập thủ công trước

## 📈 Monitoring

### Log files
- Bot logs: Hiển thị trong terminal
- Backend logs: Hiển thị trong terminal
- Database: `crm_facebook.db`

### Trạng thái hệ thống
- Backend: `http://localhost:5000/api/fb_accounts`
- Bot status: Hiển thị trong giao diện web
- Database: SQLite browser

## 🔒 Bảo mật

### Mã hóa mật khẩu
- Mật khẩu được mã hóa bằng Fernet
- Key lưu trong file `encryption.key`
- Không lưu plain text password

### Database
- SQLite với proper indexing
- Backup định kỳ file `crm_facebook.db`
- Không chia sẻ file database

### Network
- CORS được cấu hình đúng
- Chỉ chạy trên localhost
- Không expose ra internet

## 🚨 Lưu ý quan trọng

### Sử dụng có trách nhiệm
- Tuân thủ Terms of Service của Facebook
- Không spam hoặc lạm dụng
- Sử dụng với tần suất hợp lý

### Bảo mật tài khoản
- Không chia sẻ thông tin đăng nhập
- Bảo vệ file `user_accounts.json`
- Thay đổi mật khẩu định kỳ

### Backup dữ liệu
- Backup file `crm_facebook.db`
- Backup file `user_accounts.json`
- Backup file `encryption.key`

## 📞 Hỗ trợ

Nếu gặp vấn đề:
1. Kiểm tra logs trong terminal
2. Kiểm tra console browser
3. Kiểm tra kết nối network
4. Restart hệ thống

---

**Lưu ý**: Hệ thống này được phát triển cho mục đích học tập và nghiên cứu. Sử dụng có trách nhiệm và tuân thủ các quy định pháp luật. 