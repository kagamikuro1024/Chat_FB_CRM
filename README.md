# CRM Facebook Management System

Hệ thống quản lý tài khoản Facebook tích hợp vào CRM với khả năng gửi tin nhắn và đăng bài theo thời gian thực.

## Tính năng chính

- ✅ Quản lý nhiều tài khoản Facebook tập trung
- ✅ Theo dõi trạng thái online/offline theo thời gian thực
- ✅ Tự động cào và hiển thị tin nhắn mới từ Facebook
- ✅ Gửi tin nhắn trả lời thông qua giao diện CRM
- ✅ Đăng bài viết mới lên Facebook từ CRM
- ✅ Giao diện web hiện đại và dễ sử dụng
- ✅ Bảo mật thông tin đăng nhập với mã hóa

## Cấu trúc hệ thống

```
CRM Facebook Management/
├── crm_backend.py          # Flask + SocketIO Backend
├── toolfacebook.py         # Facebook Bot (Selenium)
├── crm_frontend.html       # Giao diện web
├── requirements.txt         # Thư viện Python
├── user_accounts.json      # Cấu hình tài khoản
└── README.md              # Hướng dẫn sử dụng
```

## Cài đặt và chạy

### 1. Cài đặt thư viện

```bash
pip install -r requirements.txt
```

### 2. Cấu hình tài khoản Facebook

Tạo file `user_accounts.json`:

```json
[
  {
    "user_id_chat": "account1",
    "facebook_username": "your_facebook_username",
    "facebook_password": "your_facebook_password",
    "facebook_2fa_code": "your_2fa_code_if_needed"
  },
  {
    "user_id_chat": "account2", 
    "facebook_username": "another_facebook_username",
    "facebook_password": "another_facebook_password",
    "facebook_2fa_code": ""
  }
]
```

### 3. Khởi động CRM Backend

```bash
python crm_backend.py
```

Backend sẽ chạy tại: `http://localhost:5000`

### 4. Khởi động Facebook Bot

Cho mỗi tài khoản Facebook, chạy một instance bot:

```bash
# Terminal 1 - Bot cho account1
python toolfacebook.py account1

# Terminal 2 - Bot cho account2  
python toolfacebook.py account2
```

### 5. Mở giao diện web

Mở file `crm_frontend.html` trong trình duyệt hoặc chạy:

```bash
# Nếu có Python HTTP server
python -m http.server 8000
# Sau đó mở: http://localhost:8000/crm_frontend.html
```

## Hướng dẫn sử dụng

### Quản lý tài khoản

1. **Thêm tài khoản mới**: Sử dụng API POST `/api/fb_accounts`
2. **Xem trạng thái**: Giao diện hiển thị trạng thái online/offline theo thời gian thực
3. **Theo dõi hoạt động**: Bot tự động báo cáo trạng thái về Backend

### Quản lý tin nhắn

1. **Xem tin nhắn mới**: Bot tự động cào tin nhắn và hiển thị trong CRM
2. **Gửi tin nhắn trả lời**: 
   - Chọn tài khoản Facebook
   - Chọn cuộc hội thoại
   - Nhập tin nhắn và nhấn "Gửi"
3. **Theo dõi lịch sử**: Tất cả tin nhắn được lưu trong database

### Đăng bài viết

1. **Chuyển sang tab "Đăng bài"**
2. **Chọn tài khoản Facebook** để đăng bài
3. **Nhập nội dung bài viết**
4. **Nhấn "Đăng bài"** - Bot sẽ tự động đăng lên Facebook
5. **Theo dõi trạng thái** - Hệ thống báo cáo thành công/thất bại

## API Endpoints

### REST API

- `GET /api/fb_accounts` - Lấy danh sách tài khoản
- `POST /api/fb_accounts` - Thêm tài khoản mới
- `GET /api/conversations/<user_id_chat>` - Lấy cuộc hội thoại
- `GET /api/messages/<conversation_id>` - Lấy tin nhắn
- `POST /api/send_message_from_crm` - Gửi tin nhắn
- `POST /api/post_to_facebook` - Đăng bài

### Socket.IO Events

**Bot → Backend:**
- `bot_register` - Bot đăng ký
- `new_messages` - Tin nhắn mới
- `post_status_update` - Trạng thái đăng bài

**Backend → Bot:**
- `send_message_command` - Lệnh gửi tin nhắn
- `post_news_feed_command` - Lệnh đăng bài

**Backend → Frontend:**
- `bot_status_update` - Cập nhật trạng thái bot
- `crm_new_message` - Tin nhắn mới
- `crm_post_status` - Trạng thái đăng bài

## Cấu trúc Database

### Bảng `facebook_accounts`
- `id` - Primary key
- `user_id_chat` - ID duy nhất của tài khoản
- `username` - Tên đăng nhập Facebook
- `encrypted_password` - Mật khẩu đã mã hóa
- `two_fa_code` - Mã 2FA (nếu có)
- `is_active` - Trạng thái hoạt động
- `last_online` - Thời gian online cuối

### Bảng `conversations`
- `id` - Primary key
- `facebook_account_id` - Foreign key tới facebook_accounts
- `participant_name` - Tên người tham gia
- `participant_url` - URL profile người tham gia
- `conversation_url` - URL cuộc hội thoại
- `unread_count` - Số tin nhắn chưa đọc
- `last_message_timestamp` - Thời gian tin nhắn cuối

### Bảng `messages`
- `id` - Primary key
- `conversation_id` - Foreign key tới conversations
- `sender_name` - Tên người gửi
- `content` - Nội dung tin nhắn
- `is_from_crm` - Tin nhắn từ CRM hay Facebook
- `timestamp` - Thời gian gửi
- `is_read` - Đã đọc chưa

### Bảng `posts`
- `id` - Primary key
- `facebook_account_id` - Foreign key tới facebook_accounts
- `content` - Nội dung bài viết
- `status` - Trạng thái (pending/posted/failed)
- `created_at` - Thời gian tạo
- `posted_at` - Thời gian đăng

## Bảo mật

- **Mã hóa mật khẩu**: Sử dụng Fernet encryption
- **Key management**: Tự động tạo và quản lý encryption key
- **Database security**: SQLite với proper indexing
- **Network security**: CORS được cấu hình đúng cách

## Troubleshooting

### Bot không kết nối được
1. Kiểm tra CRM Backend có đang chạy không
2. Kiểm tra thông tin tài khoản trong `user_accounts.json`
3. Kiểm tra kết nối internet

### Tin nhắn không gửi được
1. Kiểm tra bot có online không
2. Kiểm tra URL participant có đúng không
3. Kiểm tra Facebook có yêu cầu xác thực không

### Đăng bài thất bại
1. Kiểm tra bot có online không
2. Kiểm tra nội dung bài viết có vi phạm chính sách Facebook không
3. Kiểm tra tài khoản có bị hạn chế không

### Giao diện không cập nhật
1. Kiểm tra kết nối Socket.IO
2. Refresh trang web
3. Kiểm tra console browser có lỗi không

## Lưu ý quan trọng

⚠️ **Cảnh báo về việc sử dụng bot Facebook:**
- Facebook có thể phát hiện và khóa tài khoản
- Sử dụng với tần suất hợp lý
- Tuân thủ Terms of Service của Facebook
- Không sử dụng cho mục đích spam

⚠️ **Bảo mật:**
- Không chia sẻ file `user_accounts.json`
- Bảo vệ file `encryption.key`
- Sử dụng HTTPS trong production
- Thay đổi `SECRET_KEY` trong production

## Phát triển thêm

### Tính năng có thể thêm:
- [ ] Gửi file/hình ảnh
- [ ] Lập lịch đăng bài
- [ ] Phân tích thống kê
- [ ] Quản lý nhóm Facebook
- [ ] Tích hợp với CRM khác
- [ ] Mobile app

### Cải thiện kỹ thuật:
- [ ] Sử dụng PostgreSQL thay vì SQLite
- [ ] Docker containerization
- [ ] Load balancing cho nhiều bot
- [ ] Monitoring và logging
- [ ] Unit tests
- [ ] CI/CD pipeline

## Liên hệ

Nếu có vấn đề hoặc cần hỗ trợ, vui lòng tạo issue hoặc liên hệ qua email.

---

**Lưu ý**: Hệ thống này được phát triển cho mục đích học tập và nghiên cứu. Sử dụng có trách nhiệm và tuân thủ các quy định pháp luật.