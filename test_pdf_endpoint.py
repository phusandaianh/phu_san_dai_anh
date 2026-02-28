#!/usr/bin/env python3
"""
Test script for PDF generation endpoint
"""
import requests
import json

def test_pdf_endpoint():
    """Test the PDF generation endpoint"""
    url = "http://127.0.0.1:5000/api/generate-clinical-form-pdf"
    
    # Sample HTML content
    test_content = """
    <h2 style="color:#0000cc; margin:0;">PHIẾU CHỈ ĐỊNH CẬN LÂM SÀNG</h2>
    <table style="width:100%; border-collapse:collapse; margin-bottom:20px;">
        <tr>
            <td style="padding:8px; border:1px solid #000; width:20%;"><strong>Họ tên:</strong></td>
            <td style="padding:8px; border:1px solid #000; width:30%;">Nguyễn Văn A</td>
            <td style="padding:8px; border:1px solid #000; width:20%;"><strong>Tuổi:</strong></td>
            <td style="padding:8px; border:1px solid #000; width:30%;">25</td>
        </tr>
    </table>
    <div style="margin-bottom:20px;">
        <h3 style="color:#0000cc; margin-bottom:10px;">CHỈ ĐỊNH XÉT NGHIỆM:</h3>
        <div style="border:1px solid #000; padding:10px; min-height:100px;">
            <p>□ Siêu âm ổ bụng</p>
            <p>□ Siêu âm tử cung phần phụ</p>
            <p>□ Xét nghiệm máu</p>
        </div>
    </div>
    """
    
    data = {
        "content": test_content,
        "filename": "Test_Nguyen_Van_A_1998.25.10.2025.pdf",
        "appointment_id": 1
    }
    
    try:
        response = requests.post(url, json=data, timeout=30)
        
        if response.status_code == 200:
            print("✅ PDF generation successful!")
            print(f"Content-Type: {response.headers.get('Content-Type')}")
            print(f"Content-Length: {len(response.content)} bytes")
            
            # Save the PDF to a file for inspection
            with open("test_output.pdf", "wb") as f:
                f.write(response.content)
            print("📄 PDF saved as 'test_output.pdf'")
            
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    print("Testing PDF generation endpoint...")
    test_pdf_endpoint()
