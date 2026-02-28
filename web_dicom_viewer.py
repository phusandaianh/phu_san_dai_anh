from flask import Flask, render_template_string, render_template, send_file
from pathlib import Path
import pydicom
from PIL import Image
import io, os

# Thư mục chứa DICOM
BASE_DIR = Path("received_dicoms")

# Khởi tạo Flask
app = Flask(__name__)

# ===================== HTML Template =====================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>DICOM Viewer - Voluson E10</title>
  <style>
    body { font-family: Arial; background: #f6f8fa; margin: 0; padding: 20px; }
    h1 { color: #2c3e50; }
    .patient { background: white; padding: 10px; margin-bottom: 15px; border-radius: 8px; box-shadow: 0 0 5px #ccc; }
    .images img { width: 150px; margin: 5px; border-radius: 8px; border: 1px solid #aaa; }
    .images { display: flex; flex-wrap: wrap; }
  </style>
</head>
<body>
  <h1>🩻 DICOM Viewer - Voluson E10</h1>
  {% for patient, files in data.items() %}
    <div class="patient">
      <h2>👤 {{ patient }}</h2>
      <div class="images">
        {% for f in files %}
          <a href="/viewer/{{ patient }}/{{ f }}" title="Mở đo đạc trực tiếp"><img src="/preview/{{ patient }}/{{ f }}"></a>
        {% endfor %}
      </div>
    </div>
  {% endfor %}
</body>
</html>
"""

# ===================== ROUTES =====================
@app.route('/')
def index():
    data = {}
    for patient_dir in sorted(BASE_DIR.glob("*")):
        if patient_dir.is_dir():
            dicoms = [f.name for f in patient_dir.glob("*.dcm")]
            data[patient_dir.name] = sorted(dicoms)
    return render_template_string(HTML_TEMPLATE, data=data)

@app.route('/preview/<patient>/<filename>')
def preview(patient, filename):
    """Trả về ảnh PNG thu nhỏ"""
    dicom_path = BASE_DIR / patient / filename
    try:
        ds = pydicom.dcmread(dicom_path)
        if hasattr(ds, "pixel_array"):
            img = Image.fromarray(ds.pixel_array)
            img.thumbnail((300, 300))
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            buf.seek(0)
            return send_file(buf, mimetype='image/png')
        else:
            return "No pixel data", 404
    except Exception as e:
        return f"Lỗi đọc DICOM: {e}", 500

@app.route('/dicom/<patient>/<filename>')
def get_dicom(patient, filename):
    """Trả về file DICOM gốc để Cornerstone tải qua WADO-URI giả lập"""
    dicom_path = BASE_DIR / patient / filename
    if not dicom_path.exists():
        return "Không tìm thấy file", 404
    try:
        # Trả về đúng MIME cho DICOM
        return send_file(str(dicom_path), mimetype='application/dicom')
    except Exception as e:
        return f"Lỗi gửi DICOM: {e}", 500

@app.route('/view/<patient>/<filename>')
def view_full(patient, filename):
    """Hiển thị ảnh full"""
    dicom_path = BASE_DIR / patient / filename
    ds = pydicom.dcmread(dicom_path)
    if hasattr(ds, "pixel_array"):
        img = Image.fromarray(ds.pixel_array)
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        return send_file(buf, mimetype='image/png')
    else:
        return "Không có dữ liệu ảnh trong file DICOM này.", 404

@app.route('/viewer/<patient>/<filename>')
def interactive_viewer(patient, filename):
    """Trang viewer sử dụng Cornerstone + công cụ đo đạc"""
    # Dùng template inline để giảm phụ thuộc
    return render_template('dicom_viewer.html', patient=patient, filename=filename)

# ===================== MAIN =====================
if __name__ == '__main__':
    print("🌐 DICOM Web Viewer chạy tại: http://localhost:5000")
    print("📂 Thư mục dữ liệu:", BASE_DIR.resolve())
    app.run(host='0.0.0.0', port=5000, debug=False)
