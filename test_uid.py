#!/usr/bin/env python3
"""
Test DICOM UID - Tim loi UID
"""

import sys

def test_uid():
    """Test UID"""
    print("Test DICOM UID...")
    
    try:
        from pydicom import uid
        from pydicom.uid import UID
        
        # Test generate UID
        test_uid = uid.generate_uid()
        print(f"OK: Generate UID: {test_uid}")
        
        # Test create UID from string
        uid_str = "1.2.840.10008.5.1.4.31"  # Modality Worklist Find SOP Class
        test_uid2 = UID(uid_str)
        print(f"OK: Create UID from string: {test_uid2}")
        
        # Test VerificationPresentationContexts
        from pynetdicom import VerificationPresentationContexts
        print(f"OK: VerificationPresentationContexts imported")
        
        return True
        
    except Exception as e:
        print(f"LOI: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("TEST DICOM UID")
    print("=" * 60)
    
    success = test_uid()
    
    print("\n" + "=" * 60)
    if success:
        print("OK: TEST THANH CONG!")
    else:
        print("FAIL: TEST THAT BAI!")
    
    sys.exit(0 if success else 1)
