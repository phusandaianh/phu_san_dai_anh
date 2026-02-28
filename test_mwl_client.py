import logging
from pydicom.dataset import Dataset
from pynetdicom import AE
from pynetdicom.sop_class import ModalityWorklistInformationFind
import sys

def test_mwl_query(host='127.0.0.1', port=11112):
    """Test MWL server bằng cách gửi C-FIND request"""
    # Tạo application entity
    ae = AE(ae_title=b'TEST_SCU')
    ae.add_requested_context(ModalityWorklistInformationFind)
    
    print(f"Connecting to {host}:{port}...")
    
    # Tạo dataset cho query
    ds = Dataset()
    # Thêm SpecificCharacterSet để hỗ trợ Unicode
    ds.SpecificCharacterSet = 'ISO_IR 192'
    ds.PatientName = ''  # Query tất cả tên
    ds.QueryRetrieveLevel = 'PATIENT'
    
    # Thêm các trường cần thiết cho MWL query
    ds.ScheduledProcedureStepSequence = [Dataset()]
    ds.ScheduledProcedureStepSequence[0].ScheduledStationAETitle = ''
    ds.ScheduledProcedureStepSequence[0].ScheduledProcedureStepStartDate = ''
    ds.ScheduledProcedureStepSequence[0].Modality = ''
    
    # Enable debug logging for pynetdicom
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('pynetdicom').setLevel(logging.DEBUG)

    try:
        # Thực hiện query
        print(f"Attempting to associate with {host}:{port} (Called AE: MWL_SCP)")
        assoc = ae.associate(host, port, ae_title=b'MWL_SCP')

        if assoc.is_established:
            print("Association established successfully!")

            # Gửi C-FIND request
            responses = assoc.send_c_find(ds, ModalityWorklistInformationFind)

            # In kết quả
            found = False
            for (status, identifier) in responses:
                # Some responses may not include an identifier (e.g., final status)
                if identifier and status.Status in (0xFF00, 0xFF01):
                    found = True
                    print("Tìm thấy worklist entry:")
                    print(f"  Tên BN: {getattr(identifier, 'PatientName', None)}")
                    print(f"  ID: {getattr(identifier, 'PatientID', None)}")
                    print(f"  Ngày sinh: {getattr(identifier, 'PatientBirthDate', None)}")
                    print(f"  Mô tả: {getattr(identifier, 'StudyDescription', None)}")
                    print(f"  Thời gian hẹn: {getattr(identifier, 'ScheduledProcedureStepStartDate', None)}")
                    print("-" * 40)

            if not found:
                print("Không tìm thấy worklist entries nào")

            # Release the association
            assoc.release()
        else:
            print(f"Association failed. Reason: {getattr(assoc, 'rejected_reason', 'unknown')}")
    except Exception as e:
        print(f"Error: {str(e)}")
        if assoc.is_established:
            assoc.abort()

if __name__ == "__main__":
    # Cho phép truyền host/port qua command line
    host = sys.argv[1] if len(sys.argv) > 1 else '127.0.0.1'
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 11112
    
    test_mwl_query(host, port)
