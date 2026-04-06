#!/usr/bin/env python3
"""
Script test đồng bộ máy siêu âm - Test đơn giản
Test xem có thể kết nối và gửi dữ liệu đến máy siêu âm không
"""

import sys
import json
from datetime import datetime

def test_simple_dicom_sync():
    """Test đồng bộ DICOM đơn giản"""
    print("🏥 TEST ĐỒNG BỘ MÁY SIÊU ÂM")
    print("=" * 60)
    
    try:
        # Import pynetdicom
        from pynetdicom import AE, QueryRetrievePresentationContexts
        from pydicom.dataset import Dataset
        from pydicom.uid import generate_uid
        
        print("✅ Import DICOM libraries thành công")
        
        # Đọc cấu hình
        with open('Maysieuam_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        ultrasound_ip = config['Maysieuam_ip']
        ultrasound_port = config['Maysieuam_port']
        ultrasound_ae_title = config['Maysieuam_ae_title']
        ae_title = config['ae_title']
        
        print(f"📋 Cấu hình:")
        print(f"   IP máy siêu âm: {ultrasound_ip}")
        print(f"   Port: {ultrasound_port}")
        print(f"   AE Title (máy): {ultrasound_ae_title}")
        print(f"   Clinic AE Title: {ae_title}")
        print()
        
        # Tạo AE
        ae = AE(ae_title=ae_title)
        print(f"✅ Tạo AE thành công: {ae.ae_title}")
        
        # Thêm presentation contexts cho Worklist
        from pynetdicom.sop_class import ModalityWorklistInformationFind as MWLFind
        ae.add_requested_context(MWLFind)
        
        print(f"✅ Thêm presentation contexts thành công")
        print()
        
        # Test kết nối
        print(f"🔍 Đang kết nối đến {ultrasound_ip}:{ultrasound_port}...")
        assoc = ae.associate(ultrasound_ip, ultrasound_port, ae_title=ultrasound_ae_title)
        
        if assoc.is_established:
            print(f"✅ DICOM Association thành công!")
            print(f"   Remote AE Title: {assoc.remote_ae_title}")
            print(f"   Remote Address: {assoc.remote_address}")
            print()
            
            # Test gửi worklist query
            print("🔍 Test gửi Worklist Query...")
            
            # Tạo query dataset
            query = Dataset()
            query.PatientName = ''
            query.ScheduledProcedureStepSequence = [Dataset()]
            query.ScheduledProcedureStepSequence[0].Modality = 'US'
            
            # Gửi query
            try:
                responses = assoc.send_c_find(query, MWLFind)
                print("✅ Gửi Worklist Query thành công!")
                
                # Xử lý responses
                count = 0
                for (status, ds) in responses:
                    if status:
                        print(f'✅ Status: {hex(status.Status)}')
                        if ds:
                            count += 1
                    else:
                        print(f"❌ Status: None")
                
                print(f"📊 Số worklist entries: {count}")
                
            except Exception as query_error:
                print(f"❌ Lỗi khi gửi Worklist Query: {query_error}")
            
            # Release association
            assoc.release()
            print()
            print("✅ Test DICOM hoàn thành!")
            
        else:
            print(f"❌ DICOM Association thất bại")
            print("⚠️ Không thể kết nối đến máy siêu âm")
            print()
            print("🔧 Cần kiểm tra:")
            print("   1. Máy siêu âm đã bật chưa?")
            print("   2. AE Title có khớp không?")
            print("   3. DICOM service đã được cấu hình đúng chưa?")
            return False
            
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        print(f"   Chi tiết: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = test_simple_dicom_sync()
    
    if success:
        print("\n🎉 TEST THÀNH CÔNG!")
    else:
        print("\n⚠️ TEST THẤT BẠI!")
        
    sys.exit(0 if success else 1)
