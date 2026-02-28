#!/usr/bin/env python3
"""
DICOM Server cho he thong phong kham
Nhan va xu ly worklist requests tu may Voluson
"""

from pynetdicom import AE, evt, VerificationPresentationContexts
from pynetdicom.sop_class import ModalityWorklistInformationFind as MWLFind
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('dicom_server')


def handle_worklist_request(event):
    """Xử lý Worklist request"""
    logger.info("Nhận được Worklist request từ Voluson")

    dataset = event.identifier
    logger.info(f"Nội dung Worklist query: {dataset}")

    # Trả về danh sách kết quả rỗng hoặc lấy từ database
    return []


def handle_verification_request(event):
    """Xử lý Verification request (C-ECHO)"""
    logger.info("Nhận được Verification request (C-ECHO)")
    return 0x0000  # Thành công


def start_dicom_server():
    """Khởi động DICOM Server"""
    ae = AE(ae_title='CLINIC_SYSTEM')

    # Hỗ trợ Modality Worklist và Verification
    ae.add_supported_context(MWLFind)
    for context in VerificationPresentationContexts:
        ae.add_supported_context(context)

    # Đăng ký handler cho các event
    handlers = [
        (evt.EVT_C_ECHO, handle_verification_request),
        (evt.EVT_C_FIND, handle_worklist_request),
    ]

    logger.info("============================================================")
    logger.info("Bắt đầu DICOM server trên port 104...")
    logger.info("AE Title: CLINIC_SYSTEM")
    logger.info("Đang lắng nghe kết nối từ Voluson E10...")
    logger.info("============================================================")

    ae.start_server(('0.0.0.0', 104), block=True, evt_handlers=handlers)


if __name__ == "__main__":
    print("DICOM Server cho he thong phong kham")
    print("=" * 60)
    print("AE Title: CLINIC_SYSTEM")
    print("Port: 104")
    print("Listening for connections...")
    print("=" * 60)
    print()

    try:
        start_dicom_server()
    except KeyboardInterrupt:
        print("\nStopping DICOM server...")
    except Exception as e:
        logger.error(f"Lỗi: {e}")
        import traceback
        traceback.print_exc()
