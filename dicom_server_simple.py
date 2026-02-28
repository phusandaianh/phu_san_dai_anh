#!/usr/bin/env python3
"""
DICOM Server don gian cho he thong phong kham
"""

from pynetdicom import AE
from pynetdicom.sop_class import (
    ModalityWorklistInformationFind as MWLFind,
    VerificationPresentationContext
)
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('dicom_server')

def handle_c_echo(event):
    """Xu ly C-ECHO request"""
    logger.info("Nhan duoc C-ECHO request")
    return 0x0000  # Success

def handle_c_find(event):
    """Xu ly C-FIND request (worklist)"""
    logger.info("Nhan duoc C-FIND request")
    # Tra ve empty list de test
    return []

if __name__ == "__main__":
    print("DICOM Server don gian")
    print("=" * 60)
    
    # Tao AE
    ae = AE(ae_title='CLINIC_SYSTEM')
    
    # Add contexts - Them Verification de phuc vu C-ECHO request
    ae.add_supported_context(VerificationPresentationContext)
    ae.add_supported_context(MWLFind)
    
    # Dang ky handlers
    ae.on_c_echo = handle_c_echo
    ae.on_c_find = handle_c_find
    
    print("AE Title: CLINIC_SYSTEM")
    print("Port: 104")
    print("Dang khoi dong server...")
    print("=" * 60)
    
    try:
        # Start server
        ae.start_server(('0.0.0.0', 104), block=True)
    except KeyboardInterrupt:
        print("\nDung server...")
    except Exception as e:
        logger.error(f"Loi: {e}")
        import traceback
        traceback.print_exc()
