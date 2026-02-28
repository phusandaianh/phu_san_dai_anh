from pynetdicom import AE
from pynetdicom.sop_class import ModalityWorklistInformationFind
from pydicom.dataset import Dataset

# Thông tin server Worklist
SERVER_IP = '10.17.2.2'          # Địa chỉ máy chủ MWL
SERVER_PORT = 104                # Cổng MWL server đang lắng nghe
SERVER_AE_TITLE = 'CLINIC_SYSTEM'  # AE Title của server
CALLING_AE_TITLE = 'TEST_CLIENT'   # AE Title giả lập của máy client

ae = AE(ae_title=CALLING_AE_TITLE)
ae.add_requested_context(ModalityWorklistInformationFind)

ds = Dataset()
ds.PatientName = ''     # Rỗng để lấy tất cả
ds.Modality = 'US'      # Truy vấn theo modality siêu âm

assoc = ae.associate(SERVER_IP, SERVER_PORT, ae_title=SERVER_AE_TITLE)

if assoc.is_established:
    print("✅ Kết nối thành công với server MWL")
    responses = assoc.send_c_find(ds, ModalityWorklistInformationFind)

    found = False
    for (status, identifier) in responses:
        if status and status.Status in [0xFF00, 0xFF01]:
            found = True
            print("📄 Nhận được một entry:")
            print(identifier)
        elif status and status.Status == 0x0000:
            print("✅ Kết thúc truy vấn (no more matches)")

    if not found:
        print("⚠️ Không có dữ liệu Worklist phù hợp.")

    assoc.release()
else:
    print("❌ Không thể kết nối đến server MWL")
