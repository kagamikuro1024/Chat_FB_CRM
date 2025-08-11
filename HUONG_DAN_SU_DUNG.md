# Hướng dẫn sử dụng CRM Facebook Management System

## Tổng quan

Hệ thống CRM Facebook Management được thiết kế để:
- Cào tin nhắn từ Facebook Messenger
- Hiển thị tin nhắn trên giao diện CRM
- Hỗ trợ hiển thị tin nhắn reply
- Quản lý nhiều tài khoản Facebook

## Cấu trúc dữ liệu

### File `db_tin_nhan.json`
```json
{
    "7518886718170946": {
        "sender": "Quang Trung",
        "last_message": "23h",
        "last_message_time": "23 hours ago",
        "last_5_messages": [
            {
                "sender": "Trung",
                "content": "123451212"
            },
            {
                "sender": "Tôi",
                "content": "hehe",
                "replied_content": "123451211",
                "replied_to": "Tôi"
            }
        ]
    }
}
```

## Cách chạy test

### Bước 1: Cài đặt dependencies
```bash
pip install -r requirements.txt
```

### Bước 2: Chạy test system
```bash
python test_system.py
```

Script này sẽ:
1. Khởi động CRM Backend (port 5000)
2. Load dữ liệu từ `db_tin_nhan.json`
3. Gửi dữ liệu về CRM Backend qua Socket.IO
4. Mở giao diện frontend

### Bước 3: Xem kết quả
- Mở file `crm_frontend.html` trong trình duyệt
- Chọn tài khoản "test_account"
- Xem cuộc trò chuyện với "Quang Trung"
- Kiểm tra tin nhắn reply được hiển thị đúng

## Các file chính

### 1. `toolfacebook_split.py`
- Bot cào tin nhắn từ Facebook
- Kết nối với CRM Backend qua Socket.IO
- Gửi dữ liệu tin nhắn về CRM

### 2. `crm_backend.py`
- Flask + Socket.IO Backend
- Xử lý dữ liệu tin nhắn
- Lưu vào SQLite database
- Gửi dữ liệu tới frontend

### 3. `test_load_messages.py`
- Script test để load dữ liệu từ JSON
- Gửi dữ liệu về CRM Backend

### 4. `crm_frontend.html`
- Giao diện web CRM
- Hiển thị tin nhắn và reply
- Kết nối real-time với backend

## Luồng hoạt động

```
1. Facebook Bot cào tin nhắn
   ↓
2. Lưu vào db_tin_nhan.json
   ↓
3. Gửi qua Socket.IO tới CRM Backend
   ↓
4. CRM Backend lưu vào SQLite
   ↓
5. Gửi tới Frontend qua Socket.IO
   ↓
6. Frontend hiển thị tin nhắn
```

## Test với dữ liệu có sẵn

### Chạy test đơn giản:
```bash
# Terminal 1: Khởi động CRM Backend
python crm_backend.py

# Terminal 2: Test với dữ liệu có sẵn
python test_load_messages.py test_account

# Terminal 3: Mở frontend
# Mở file crm_frontend.html trong trình duyệt
```

### Kết quả mong đợi:
1. CRM Backend chạy trên http://localhost:5000
2. Tài khoản "test_account" xuất hiện trong danh sách
3. Cuộc trò chuyện với "Quang Trung" hiển thị
4. 5 tin nhắn gần nhất được hiển thị
5. Tin nhắn reply có phần "Reply to..." hiển thị

## Troubleshooting

### Lỗi kết nối Socket.IO
- Kiểm tra CRM Backend có chạy không
- Kiểm tra port 5000 có bị chiếm không
- Xem console browser có lỗi không

### Không hiển thị tin nhắn
- Kiểm tra file `db_tin_nhan.json` có dữ liệu không
- Kiểm tra script `test_load_messages.py` có chạy thành công không
- Xem log của CRM Backend

### Frontend không cập nhật
- Refresh trang web
- Kiểm tra kết nối Socket.IO
- Xem console browser

## Cấu trúc database

### Bảng `facebook_accounts`
- `id`: Primary key
- `user_id_chat`: ID tài khoản
- `username`: Tên đăng nhập
- `encrypted_password`: Mật khẩu đã mã hóa
- `is_active`: Trạng thái hoạt động

### Bảng `conversations`
- `id`: Primary key
- `facebook_account_id`: Foreign key
- `participant_name`: Tên người tham gia
- `participant_url`: URL profile
- `conversation_url`: URL cuộc trò chuyện
- `unread_count`: Số tin nhắn chưa đọc

### Bảng `messages`
- `id`: Primary key
- `conversation_id`: Foreign key
- `sender_name`: Tên người gửi
- `content`: Nội dung tin nhắn
- `is_from_crm`: Tin nhắn từ CRM hay Facebook
- `timestamp`: Thời gian gửi

## Phát triển thêm

### Tính năng có thể thêm:
- [ ] Gửi tin nhắn từ CRM
- [ ] Đăng bài lên Facebook
- [ ] Quản lý nhiều tài khoản
- [ ] Thống kê tin nhắn
- [ ] Tìm kiếm tin nhắn

### Cải thiện kỹ thuật:
- [ ] Sử dụng PostgreSQL
- [ ] Docker containerization
- [ ] Load balancing
- [ ] Monitoring và logging
- [ ] Unit tests

## Lưu ý quan trọng

⚠️ **Cảnh báo về việc sử dụng bot Facebook:**
- Facebook có thể phát hiện và khóa tài khoản
- Sử dụng với tần suất hợp lý
- Tuân thủ Terms of Service của Facebook
- Không sử dụng cho mục đích spam

⚠️ **Bảo mật:**
- Không chia sẻ file cookies
- Bảo vệ thông tin đăng nhập
- Sử dụng HTTPS trong production
- Thay đổi SECRET_KEY trong production
