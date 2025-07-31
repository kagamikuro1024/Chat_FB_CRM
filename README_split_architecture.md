# CRM Facebook Management - Split Architecture

Hệ thống CRM Facebook với kiến trúc API tách biệt, chia thành 2 phần riêng biệt:
- **API Receiver**: Nhận tin nhắn và thông báo từ Facebook Bot
- **API Sender**: Gửi lệnh từ CRM đến Facebook Bot

## Kiến trúc hệ thống

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │  API Receiver   │    │  API Sender     │
│   (Port 8000)   │◄──►│   (Port 5001)   │    │   (Port 5002)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       ▲                       ▲
         │                       │                       │
         ▼                       │                       │
┌─────────────────┐              │                       │
│  Facebook Bot   │──────────────┴───────────────────────┘
│  (Split Mode)   │
└─────────────────┘
```

## Các thành phần

### 1. API Receiver (`api_receiver.py`)
- **Port**: 5001
- **Chức năng**: 
  - Nhận tin nhắn mới từ Facebook Bot
  - Nhận thông báo mới từ Facebook Bot
  - Lưu trữ dữ liệu vào database
  - Thông báo real-time cho Frontend

**API Endpoints:**
- `POST /api/bot/register` - Bot đăng ký
- `POST /api/bot/new_messages` - Nhận tin nhắn mới
- `POST /api/bot/new_notifications` - Nhận thông báo mới
- `POST /api/bot/status_update` - Cập nhật trạng thái bot

### 2. API Sender (`api_sender.py`)
- **Port**: 5002
- **Chức năng**:
  - Cung cấp API cho Frontend
  - Gửi lệnh đến Facebook Bot
  - Quản lý tài khoản và cuộc hội thoại
  - Chuyển tiếp events từ Receiver API

**API Endpoints:**
- `GET /api/fb_accounts` - Lấy danh sách tài khoản
- `GET /api/conversations/<user_id_chat>` - Lấy cuộc hội thoại
- `GET /api/messages/<conversation_id>` - Lấy tin nhắn
- `POST /api/send_message_from_crm` - Gửi tin nhắn
- `POST /api/post_to_facebook` - Đăng bài
- `GET /api/notifications/<user_id_chat>` - Lấy thông báo

### 3. Facebook Bot Split (`toolfacebook_split.py`)
- **Chức năng**:
  - Kết nối với cả Receiver API và Sender API
  - Cào tin nhắn và thông báo từ Facebook
  - Gửi dữ liệu đến Receiver API
  - Nhận lệnh từ Sender API

### 4. Frontend Split (`crm_frontend_split.html`)
- **Chức năng**:
  - Giao diện web cho người dùng
  - Kết nối với Sender API
  - Hiển thị trạng thái của cả 2 API
  - Real-time updates

## Cách chạy hệ thống

### 1. Khởi động API Receiver
```bash
python api_receiver.py
```
Server sẽ chạy tại: `http://localhost:5001`

### 2. Khởi động API Sender
```bash
python api_sender.py
```
Server sẽ chạy tại: `http://localhost:5002`

### 3. Khởi động Facebook Bot
```bash
python toolfacebook_split.py account1
```

### 4. Mở Frontend
Mở file `crm_frontend_split.html` trong trình duyệt

## Luồng dữ liệu

### Luồng nhận tin nhắn từ Facebook:
```
Facebook Bot → API Receiver → Database → Frontend (via Sender API)
```

1. Bot cào tin nhắn từ Facebook
2. Bot gửi tin nhắn đến Receiver API qua REST API
3. Receiver API lưu vào database
4. Receiver API emit event cho Frontend
5. Sender API chuyển tiếp event đến Frontend

### Luồng gửi tin nhắn từ CRM:
```
Frontend → API Sender → Facebook Bot → Facebook
```

1. User nhập tin nhắn trong Frontend
2. Frontend gửi request đến Sender API
3. Sender API gửi lệnh qua Socket.IO đến Bot
4. Bot gửi tin nhắn trên Facebook

### Luồng đăng bài:
```
Frontend → API Sender → Facebook Bot → Facebook → API Sender → Frontend
```

1. User tạo bài đăng trong Frontend
2. Sender API lưu bài đăng vào database
3. Sender API gửi lệnh đến Bot
4. Bot đăng bài trên Facebook
5. Bot báo cáo kết quả về Sender API
6. Sender API thông báo cho Frontend

## Ưu điểm của kiến trúc tách biệt

### 1. Tách biệt trách nhiệm
- **Receiver API**: Chỉ xử lý việc nhận dữ liệu từ Bot
- **Sender API**: Chỉ xử lý việc gửi lệnh đến Bot
- **Frontend**: Chỉ xử lý giao diện người dùng

### 2. Khả năng mở rộng
- Có thể scale từng API độc lập
- Dễ dàng thêm tính năng mới
- Có thể deploy riêng biệt

### 3. Bảo mật
- Tách biệt quyền truy cập
- Dễ dàng kiểm soát traffic
- Có thể áp dụng rate limiting riêng

### 4. Monitoring và Debugging
- Dễ dàng theo dõi từng API
- Có thể debug riêng từng phần
- Logs được tách biệt rõ ràng

## Cấu hình

### Database
Cả 2 API sử dụng chung database `crm_facebook.db` với các bảng:
- `facebook_accounts`
- `conversations`
- `messages`
- `notifications`
- `posts`

### Socket.IO Events

**Receiver API Events:**
- `bot_register` - Bot đăng ký
- `new_messages` - Tin nhắn mới
- `new_notifications` - Thông báo mới

**Sender API Events:**
- `send_message_command` - Lệnh gửi tin nhắn
- `post_news_feed_command` - Lệnh đăng bài
- `post_status_update` - Trạng thái đăng bài

## Troubleshooting

### API Receiver không khởi động
1. Kiểm tra port 5001 có đang được sử dụng không
2. Kiểm tra dependencies đã cài đặt chưa
3. Kiểm tra quyền ghi file database

### API Sender không khởi động
1. Kiểm tra port 5002 có đang được sử dụng không
2. Kiểm tra kết nối đến Receiver API
3. Kiểm tra file encryption.key

### Bot không kết nối được
1. Kiểm tra cả 2 API đã khởi động chưa
2. Kiểm tra thông tin tài khoản trong `user_accounts.json`
3. Kiểm tra kết nối internet

### Frontend không hiển thị dữ liệu
1. Kiểm tra kết nối Socket.IO
2. Kiểm tra CORS settings
3. Kiểm tra console browser có lỗi không

## So sánh với kiến trúc cũ

| Tính năng | Kiến trúc cũ | Kiến trúc tách biệt |
|-----------|--------------|---------------------|
| Số lượng API | 1 (Port 5000) | 2 (Port 5001, 5002) |
| Trách nhiệm | Tất cả trong 1 file | Tách biệt rõ ràng |
| Khả năng scale | Khó | Dễ dàng |
| Debugging | Phức tạp | Đơn giản |
| Bảo mật | Cơ bản | Nâng cao |
| Monitoring | Khó theo dõi | Dễ theo dõi |

## Phát triển thêm

### Tính năng có thể thêm:
- [ ] Load balancing cho các API
- [ ] Redis cache cho performance
- [ ] Message queue (RabbitMQ/Redis)
- [ ] Docker containerization
- [ ] Kubernetes deployment
- [ ] Monitoring với Prometheus/Grafana
- [ ] Logging với ELK stack

### Cải thiện kỹ thuật:
- [ ] Authentication/Authorization
- [ ] Rate limiting
- [ ] API versioning
- [ ] Swagger documentation
- [ ] Unit tests
- [ ] Integration tests
- [ ] CI/CD pipeline

## Kết luận

Kiến trúc tách biệt mang lại nhiều lợi ích về mặt scalability, maintainability và security. Việc chia nhỏ hệ thống thành các thành phần độc lập giúp dễ dàng phát triển và bảo trì trong tương lai. 