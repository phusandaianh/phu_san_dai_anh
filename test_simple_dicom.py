#!/usr/bin/env python3
"""
Script test DICOM đơn giản nhất - không dùng Presentation Contexts
"""

import sys
from pynetdicom import AE

def test_basic_association():
    """Test association co ban nhat"""
    print("Test DICOM Association co ban...")
    
    try:
        # Tao AE don gian, khong them context
        ae = AE(ae_title='CLINIC')
        print("OK: Tao AE thanh cong")
        
        print("   AE Title:", ae.ae_title)
        print("   Requested contexts:", len(ae.requested_contexts))
        
        # Thu ket noi
        print("\nDang ket noi den 10.17.2.1:104...")
        assoc = ae.associate('10.17.2.1', 104, ae_title='VOLUSON')
        
        if assoc.is_established:
            print("OK: Association thanh cong!")
            print("   Remote AE Title:", assoc.remote_ae_title)
            assoc.release()
            return True
        else:
            print("FAIL: Association that bai")
            if hasattr(assoc, 'response'):
                print("   Response:", assoc.response)
            return False
            
    except Exception as e:
        print(f"LOI: {e}")
        print(f"   Loai loi: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("TEST DICOM DON GIAN NHAT")
    print("=" * 60)
    
    success = test_basic_association()
    
    print("\n" + "=" * 60)
    if success:
        print("OK: TEST THANH CONG!")
    else:
        print("FAIL: TEST THAT BAI!")
    
    sys.exit(0 if success else 1)
