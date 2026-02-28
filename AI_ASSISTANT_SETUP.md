# AI Assistant - Hướng dẫn sử dụng

## Tổng quan
Trợ lý AI đã được tích hợp vào hệ thống Phòng khám Đại Anh. AI Assistant hỗ trợ:
- ✅ Nhận diện giọng nói tiếng Việt
- ✅ Nhập văn bản
- ✅ Luôn hiển thị trên mọi trang (floating button)
- ✅ Điều hướng giữa các trang
- ✅ Tìm kiếm bệnh nhân
- ✅ Trả lời câu hỏi

## Tích hợp vào trang HTML mới

Để thêm AI Assistant vào bất kỳ trang HTML nào, chỉ cần thêm 2 dòng sau:

### Cách 1: Tự động (khuyến nghị)
Chỉ cần thêm script trước thẻ `</body>`:
```html
<!-- AI Assistant - Luôn hiển thị trên mọi trang -->
<script src="ai-assistant.js"></script>
</body>
```

Script sẽ tự động load CSS nếu chưa có.

### Cách 2: Thủ công (nếu muốn kiểm soát tốt hơn)
Thêm vào `<head>`:
```html
<link rel="stylesheet" href="ai-assistant.css">
```

Và thêm trước `</body>`:
```html
<script src="ai-assistant.js"></script>
</body>
```

## Các lệnh hỗ trợ

### Điều hướng trang
- "Trang chủ" / "Home"
- "Danh sách khám" / "Examination list"
- "Lịch làm việc" / "Schedule"
- "Đặt lịch" / "Booking"
- "Hồ sơ bệnh án" / "Patient records"
- "VR PACS" / "Siêu âm" / "DICOM"
- "Admin" / "Quản trị"

### Tìm kiếm
- "Tìm bệnh nhân [tên]"
- "Tìm kiếm [tên]"
- "Search patient [name]"

### Thông tin
- "Giờ làm việc"
- "Dịch vụ"
- "Liên hệ"
- "Địa chỉ"

### Lệnh khác
- "Làm mới" / "Refresh"
- "Giúp tôi" / "Help"

## Sử dụng

### Bằng giọng nói
1. Click vào nút mic trong ô nhập
2. Nói lệnh bằng tiếng Việt
3. AI sẽ tự động xử lý

### Bằng văn bản
1. Click vào nút robot ở góc dưới bên phải
2. Nhập lệnh vào ô text
3. Nhấn Enter hoặc click nút gửi

### Quick Actions
Click vào các nút nhanh ở dưới cửa sổ chat:
- Tìm bệnh nhân
- Danh sách khám
- Lịch làm việc
- Trang chủ

## API Endpoint

AI Assistant sử dụng API endpoint:
```
POST /api/ai-assistant/chat
```

Body:
```json
{
    "message": "tìm kiếm bệnh nhân",
    "context": {
        "url": "/vr-pacs.html",
        "title": "VR PACS",
        "page": "vr-pacs.html"
    }
}
```

Response:
```json
{
    "success": true,
    "response": "Đang tìm kiếm...",
    "action": {
        "type": "search",
        "selector": "#searchInput",
        "value": "tên bệnh nhân"
    }
}
```

## Mở rộng

Để thêm lệnh mới, chỉnh sửa file `app.py`, hàm `ai_assistant_chat()`:

```python
elif any(keyword in message for keyword in ['lệnh mới', 'new command']):
    response_text = 'Thực hiện lệnh mới...'
    action = {'type': 'navigate', 'url': '/new-page.html'}
```

## Lưu ý

- Cần trình duyệt hỗ trợ Web Speech API cho tính năng giọng nói
- Chrome và Edge hỗ trợ tốt nhất
- Firefox cần cấu hình bổ sung
- Safari hỗ trợ hạn chế

## Troubleshooting

### Không thấy nút AI Assistant
- Kiểm tra console có lỗi JavaScript không
- Đảm bảo file `ai-assistant.js` được load
- Kiểm tra đường dẫn file CSS và JS

### Giọng nói không hoạt động
- Cho phép truy cập microphone trong trình duyệt
- Sử dụng HTTPS hoặc localhost
- Kiểm tra ngôn ngữ được set là `vi-VN`

### API không hoạt động
- Kiểm tra server Flask đang chạy
- Kiểm tra endpoint `/api/ai-assistant/chat` trong `app.py`
- Xem console để debug lỗi

## Files liên quan

- `ai-assistant.css` - Styles cho AI Assistant
- `ai-assistant.js` - Logic và UI của AI Assistant  
- `app.py` - API endpoint xử lý lệnh (hàm `ai_assistant_chat()`)

