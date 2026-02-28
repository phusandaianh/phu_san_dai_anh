#!/usr/bin/env python3
"""
Script để cập nhật template phiếu kết quả cận lâm sàng với trường "Chẩn đoán"
"""

import sqlite3
import os

def update_lab_result_template():
    """Cập nhật template phiếu kết quả cận lâm sàng trong database"""
    
    # Template mới với trường "Chẩn đoán"
    new_template = '''
<div style="font-family:'Times New Roman', serif; padding:20px;">
  <div style="text-align:center; margin-bottom:20px;">
    <h2 style="color:#0000cc; margin:0;">PHIẾU KẾT QUẢ CẬN LÂM SÀNG</h2>
  </div>
  
  <table style="width:100%; border-collapse:collapse; margin-bottom:20px;">
    <tr>
      <td style="padding:8px; border:1px solid #000; width:20%;"><strong>Họ tên:</strong></td>
      <td style="padding:8px; border:1px solid #000; width:30%;">_________________</td>
      <td style="padding:8px; border:1px solid #000; width:20%;"><strong>Tuổi:</strong></td>
      <td style="padding:8px; border:1px solid #000; width:30%;">_________________</td>
    </tr>
    <tr>
      <td style="padding:8px; border:1px solid #000;"><strong>Địa chỉ:</strong></td>
      <td style="padding:8px; border:1px solid #000;" colspan="3">_________________</td>
    </tr>
    <tr>
      <td style="padding:8px; border:1px solid #000;"><strong>Chẩn đoán:</strong></td>
      <td style="padding:8px; border:1px solid #000;" colspan="3">_________________</td>
    </tr>
  </table>

  <div style="margin-bottom:20px;">
    <h3 style="color:#0000cc; margin-bottom:10px;">KẾT QUẢ XÉT NGHIỆM:</h3>
    <div style="border:1px solid #000; padding:10px; min-height:150px;">
      <p><strong>Siêu âm:</strong></p>
      <p>Kết quả: _________________</p>
      <p>Ghi chú: _________________</p>
      <br>
      <p><strong>Xét nghiệm:</strong></p>
      <p>Kết quả: _________________</p>
      <p>Ghi chú: _________________</p>
    </div>
  </div>

  <div style="display:flex; justify-content:space-between; margin-top:30px;">
    <div style="text-align:center;">
      <p><strong>Bác sĩ thực hiện</strong></p>
      <p style="margin-top:50px;">_________________</p>
    </div>
    <div style="text-align:center;">
      <p><strong>Ngày: ___/___/_____</strong></p>
    </div>
  </div>
</div>
'''
    
    # Tìm database file
    db_files = ['clinic.db', 'instance/clinic.db']
    db_path = None
    
    for db_file in db_files:
        if os.path.exists(db_file):
            db_path = db_file
            break
    
    if not db_path:
        print("Khong tim thay database file!")
        return False
    
    try:
        # Kết nối database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"Dang cap nhat database: {db_path}")
        
        # Kiểm tra bảng clinical_form_template
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='clinical_form_template'")
        if not cursor.fetchone():
            print("Bang clinical_form_template khong ton tai!")
            return False
        
        # Tìm template phiếu kết quả
        cursor.execute("SELECT id, template_type, content_html FROM clinical_form_template WHERE template_type = 'lab-result'")
        result = cursor.fetchone()
        
        if result:
            template_id, template_type, old_content = result
            print(f"Tim thay template cu (ID: {template_id})")
            
            # Cập nhật template
            cursor.execute("""
                UPDATE clinical_form_template 
                SET content_html = ? 
                WHERE id = ?
            """, (new_template, template_id))
            
            print("Da cap nhat template phieu ket qua can lam sang!")
            
        else:
            print("Khong tim thay template phieu ket qua, tao moi...")
            
            # Tạo template mới
            cursor.execute("""
                INSERT INTO clinical_form_template (template_type, name, description, content_html, created_at)
                VALUES (?, ?, ?, ?, datetime('now'))
            """, ('lab-result', 'Phieu Ket Qua Can Lam Sang', 'Template phieu ket qua can lam sang voi truong chan doan', new_template))
            
            print("Da tao template moi!")
        
        # Commit changes
        conn.commit()
        
        # Kiểm tra kết quả
        cursor.execute("SELECT content_html FROM clinical_form_template WHERE template_type = 'lab-result'")
        updated_content = cursor.fetchone()[0]
        
        if "Chẩn đoán" in updated_content:
            print("Xac nhan: Template da co truong 'Chan doan'!")
        else:
            print("Loi: Template chua duoc cap nhat dung!")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Loi khi cap nhat database: {e}")
        return False

def main():
    print("Bat dau cap nhat template phieu ket qua can lam sang...")
    print("=" * 60)
    
    success = update_lab_result_template()
    
    print("=" * 60)
    if success:
        print("Hoan thanh! Template da duoc cap nhat voi truong 'Chan doan'")
        print("Hay restart Flask server de thay thay doi")
    else:
        print("Co loi xay ra khi cap nhat template")
    
    print("\nCac buoc tiep theo:")
    print("1. Restart Flask server: python app.py")
    print("2. Truy cap trang quan ly template")
    print("3. Kiem tra phieu ket qua can lam sang")

if __name__ == "__main__":
    main()
