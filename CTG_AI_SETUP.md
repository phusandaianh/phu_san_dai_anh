# Hướng dẫn thiết lập phân tích CTG bằng AI

## Tổng quan
Hệ thống phân tích CTG (Cardiotocography) đã được tích hợp và sẵn sàng sử dụng. Hiện tại, hệ thống đang sử dụng phân tích mô phỏng (mock analysis) để demo. Để triển khai phân tích thực tế bằng AI, bạn có thể tích hợp các công cụ sau:

## Các tùy chọn tích hợp AI

### 1. **OCR (Optical Character Recognition)**
Sử dụng để đọc các số liệu từ ảnh CTG in ra:

**a) Tesseract OCR (Miễn phí, mã nguồn mở)**
```bash
# Cài đặt Tesseract
pip install pytesseract

# Tích hợp vào app.py
import pytesseract
from PIL import Image

# Trong hàm analyze_ctg_image()
img = Image.open(image_bytes)
text = pytesseract.image_to_string(img, lang='eng')
# Parse text để tìm các giá trị CTG
```

**b) Google Cloud Vision API**
```python
from google.cloud import vision
client = vision.ImageAnnotatorClient()

response = client.text_detection(image=image_data)
texts = response.text_annotations
```

**c) Azure Computer Vision**
```python
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from msrest.authentication import CognitiveServicesCredentials

client = ComputerVisionClient(endpoint, CognitiveServicesCredentials(key))
result = client.read_in_stream(image_stream)
```

### 2. **Computer Vision để phân tích đồ thị CTG**
Sử dụng để đọc đường cong nhịp tim và cơn co tử cung từ đồ thị CTG:

**a) OpenCV + Template Matching**
```python
import cv2
import numpy as np

# Đọc ảnh CTG
img = cv2.imread(image_path)
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# Extract đường tim thai (heart rate trace)
# Extract đường cơn co (contractions trace)
# Tính toán baseline, variability, accelerations, decelerations
```

**b) Deep Learning (CNN) cho CTG Analysis**
- Sử dụng mô hình CNN được huấn luyện trên dataset CTG
- Các mô hình pretrained có sẵn trên GitHub
- Sử dụng TensorFlow/PyTorch

**c) YOLO/Object Detection**
- Detect các pattern trong CTG (accelerations, decelerations)
- Đếm số lượng và đo thời gian

### 3. **Tích hợp API có sẵn**

**a) Trình duyệt API (Web Speech Synthesis)**
- Đã tích hợp sẵn trong frontend
- Cần cài giọng đọc tiếng Việt trên hệ thống

**b) Azure Cognitive Services**
```python
from azure.cognitiveservices.vision.customvision.prediction import CustomVisionPredictionClient
from msrest.authentication import ApiKeyCredentials

credentials = ApiKeyCredentials(in_headers={"Prediction-key": prediction_key})
predictor = CustomVisionPredictionClient(endpoint, credentials)

results = predictor.classify_image(project_id, publish_iteration_name, image_data)
```

## Cách thêm vào hệ thống hiện tại

### Bước 1: Chọn giải pháp AI
Dựa trên nhu cầu và ngân sách, chọn một trong các tùy chọn trên.

### Bước 2: Cài đặt dependencies
```bash
# Ví dụ với Tesseract OCR
pip install pytesseract pillow

# Hoặc với TensorFlow cho deep learning
pip install tensorflow opencv-python numpy

# Hoặc với Azure SDK
pip install azure-cognitiveservices-vision-computervision
```

### Bước 3: Tích hợp vào app.py
Thay thế phần mock analysis trong hàm `analyze_ctg_image()`:

```python
@app.route('/api/analyze-ctg-image', methods=['POST'])
def analyze_ctg_image():
    """Phân tích ảnh CTG bằng điện toán"""
    try:
        data = request.json
        image_data = data.get('image_data')
        patient_id = data.get('patient_id')
        
        # TODO: Thay thế code dưới đây bằng AI thực tế
        # Trích xuất dữ liệu từ ảnh bằng OCR
        extracted_data = extract_ctg_data_from_image(image_data)
        
        # Hoặc sử dụng Computer Vision để phân tích đồ thị
        analysis = analyze_ctg_graph(image_data)
        
        # Tính toán kết quả
        result = calculate_analysis_score(analysis)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'message': f'Lỗi: {str(e)}'}), 500

def extract_ctg_data_from_image(image_data):
    """Trích xuất dữ liệu từ ảnh CTG bằng OCR"""
    # TODO: Implement OCR logic here
    pass

def analyze_ctg_graph(image_data):
    """Phân tích đồ thị CTG bằng Computer Vision"""
    # TODO: Implement CV logic here
    pass
```

## Ghi chú quan trọng

1. **Dữ liệu training**: Để có kết quả chính xác, cần dataset CTG lớn để train model
2. **Performance**: Computer Vision và Deep Learning đòi hỏi GPU nếu xử lý thời gian thực
3. **Bảo mật**: Ảnh y tế là dữ liệu nhạy cảm, đảm bảo tuân thủ GDPR/HIPAA
4. **Chi phí**: API cloud có thể phát sinh chi phí theo số lượng request
5. **Accuracy**: Mock analysis chỉ để demo, cần validation kỹ với bác sĩ chuyên khoa

## Tài liệu tham khảo

1. [Tesseract OCR Documentation](https://tesseract-ocr.github.io/)
2. [OpenCV Tutorial](https://docs.opencv.org/)
3. [TensorFlow Object Detection](https://www.tensorflow.org/lite/models/object_detection)
4. [Azure Computer Vision](https://docs.microsoft.com/azure/cognitive-services/computer-vision/)
5. [Google Cloud Vision](https://cloud.google.com/vision/docs)

## Liên hệ
Nếu cần hỗ trợ tích hợp, vui lòng liên hệ đội phát triển.
