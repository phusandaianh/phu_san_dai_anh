# Orthanc PACS Setup (Phong kham Dai Anh)

Orthanc da duoc cai theo kieu portable trong project.

## Vi tri cai dat

- `orthanc/bin/Orthanc.exe`
- `orthanc/plugins/OrthancExplorer2.dll`
- `orthanc/orthanc.json`
- `orthanc/db/` (luu PACS index + storage)

## Thong so dang cau hinh

- **DICOM AE Title**: `CLINIC_PACS`
- **DICOM Port**: `4242`
- **Web Port**: `8042`
- **Viewer URL (OE2)**: `http://10.17.2.2:8042/ui/app/`
- **Viewer URL (classic fallback)**: `http://10.17.2.2:8042/app/explorer.html`
- **REST URL**: `http://10.17.2.2:8042/system`
- **User**: `admin`
- **Password**: `orthanc123`

## Khoi dong

Chay:

```bat
start_orthanc.bat
```

## Test nhanh

1. Mo `http://10.17.2.2:8042/ui/` de vao viewer.
2. Tu app:
   - `POST /api/test-dicom-echo`
   - body:
   ```json
   {
     "ip": "127.0.0.1",
     "port": 4242,
     "called_ae_title": "CLINIC_PACS",
     "local_ae_title": "CLINIC_SYSTEM"
   }
   ```
3. Tren may sieu am, them dich den Storage:
   - AE: `CLINIC_PACS`
   - Host: `10.17.2.2`
   - Port: `4242`

## Luu y tich hop voi MWL

- MWL server cua he thong hien tai van theo luong rieng (`CLINIC_SYSTEM`, port do ban cau hinh cho MWL).
- Orthanc trong cau hinh nay dong vai tro **PACS Storage + Viewer**.
- May sieu am thuong can cau hinh 2 dich den:
  - **MWL Query**: MWL server (`CLINIC_SYSTEM`, MWL port)
  - **C-STORE**: Orthanc (`CLINIC_PACS`, 4242)
