# Hướng dẫn cài đặt OCR và Computer Vision

## Bước 1: Cài đặt Tesseract OCR

### Windows:
1. Tải Tesseract từ: https://github.com/UB-Mannheim/tesseract/wiki
2. Cài đặt file `.exe` (khuyến nghị: `tesseract-ocr-w64-setup-v5.x.x.exe`)
3. Ghi nhớ đường dẫn cài đặt (mặc định: `C:\Program Files\Tesseract-OCR`)
4. Thêm vào PATH hoặc cấu hình trong code

### Cấu hình Tesseract trong Python:
Tìm dòng `pytesseract.pytesseract.tesseract_cmd` trong `app.py` và cấu hình:
```python
import pytesseract
# Uncomment và sửa đường dẫn cho Windows
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

### Linux (Ubuntu/Debian):
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
sudo apt-get install libtesseract-dev
```

### macOS:
```bash
brew install tesseract
brew install tesseract-lang  # For Vietnamese language support
```

## Bước 2: Cài đặt Python dependencies

```bash
pip install -r requirements.txt
```

Hoặc cài từng package:
```bash
pip install pytesseract==0.3.10
pip install opencv-python==4.8.1.78
pip install numpy==1.24.3
pip install Pillow==10.0.0
```

## Bước 3: Kiểm tra cài đặt

Chạy test script:
```python
# test_ocr.py
import pytesseract
from PIL import Image
import cv2
import numpy as np

print("Testing OCR installation...")
print("Pytesseract version:", pytesseract.get_tesseract_version())

print("Testing OpenCV...")
print("OpenCV version:", cv2.__version__)

print("All libraries installed successfully!")
```

## Bước 4: Khởi động lại server

```bash
python app.py
```

Bạn sẽ thấy thông báo:
- `OCR and Computer Vision libraries loaded successfully.` - Cài đặt thành công
- `Warning: OCR libraries not installed...` - Cần cài lại

## Troubleshooting

### Lỗi 1: TesseractNotFoundError
**Nguyên nhân**: Tesseract chưa cài hoặc chưa trong PATH
**Giải pháp**: 
- Cài Tesseract OCR
- Thêm vào PATH hoặc cấu hình đường dẫn trong code

### Lỗi 2: Import cv2 failed
**Nguyên nhân**: OpenCV chưa cài
**Giải pháp**: `pip install opencv-python`

### Lỗi 3: Cannot find module 'numpy'
**Nguyên nhân**: NumPy chưa cài
**Giải pháp**: `pip install numpy`

## Ghi chú

- Tesseract OCR cần cài riêng trên hệ thống, không chỉ Python package
- Để đọc tiếng Việt tốt hơn, có thể cài thêm language pack
- Computer Vision analysis hiện đang dùng heuristic đơn giản
- Để có kết quả chính xác hơn, cần train model deep learning riêng
