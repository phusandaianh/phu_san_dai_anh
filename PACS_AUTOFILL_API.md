# PACS Autofill MVP API

Tai lieu nay mo ta API MVP de tu dong dien ket qua sieu am tu file DICOM da nhan.

## 1) Tu dong dien ket qua sieu am

- **Endpoint**: `POST /api/pacs/autofill-ultrasound`
- **Muc dich**: Doc file DICOM tu `received_dicoms`, trich xuat chi so do dac co ban va tao ban ghi `ultrasound_results`.

### Request body (JSON)

```json
{
  "patient_name": "Nguyen Van A",
  "filename": "US_0001.dcm",
  "appointment_id": 123,
  "patient_id": 45,
  "accession_number": "ACC-20260330-001",
  "source_ae": "VOLUSON_E10"
}
```

### Ghi chu map du lieu

- `filename` la bat buoc.
- `patient_id` uu tien map truc tiep.
- Neu khong co `patient_id`, he thong thu map theo `accession_number` qua `clinical_service.Maysieuam_accession`.
- He thong luu mapping Study vao bang `pacs_study_links`.

### Response thanh cong

```json
{
  "success": true,
  "message": "Da tu dien ket qua sieu am tu DICOM (MVP)",
  "ultrasound_result": {
    "id": 999,
    "patient_id": 45,
    "appointment_id": 123,
    "analysis_source": "dicom_autofill_mvp"
  },
  "study_link": {
    "id": 10,
    "accession_number": "ACC-20260330-001",
    "study_instance_uid": "1.2.840...."
  },
  "extracted_measurements": {
    "gestational_age": 12.3,
    "bpd": 28.1,
    "hc": 102.4,
    "ac": 88.0,
    "fl": 14.6,
    "afi": 10.1,
    "estimated_weight": 180.0
  }
}
```

### Response that bai

- `400`: Thieu `filename` hoac khong map duoc benh nhan.
- `404`: Khong tim thay file DICOM.
- `500`: Loi doc DICOM/ghi DB.

## 2) Tra cuu mapping y lenh <-> Study DICOM

- **Endpoint**: `GET /api/pacs/study-links`
- **Query**:
  - `appointment_id` (optional)
  - `accession_number` (optional)

### Vi du

- `GET /api/pacs/study-links?appointment_id=123`
- `GET /api/pacs/study-links?accession_number=ACC-20260330-001`

## 3) Luu y van hanh

- Day la MVP: cac chi so duoc trich tu DICOM keyword va regex text.
- Bat buoc bac si xac nhan lai truoc khi ky ket qua.
- Nen mo rong parser theo tung dong may (Voluson, Mindray, GE...) de dat do chinh xac cao hon.

## 4) Auto trigger tu DICOM receiver

File `dicom_receiver.py` da duoc cap nhat de goi API autofill ngay sau khi luu C-STORE thanh cong.

- Bien moi truong co the cau hinh:
  - `AUTOFILL_API_URL` (mac dinh: `http://127.0.0.1:5000/api/pacs/autofill-ultrasound`)
  - `AUTOFILL_TIMEOUT_SEC` (mac dinh: `2.5`)
- Co che la **best-effort**: neu API autofill loi, C-STORE van thanh cong, file DICOM van duoc luu.
