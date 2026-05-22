# Trien khai toan bo may trong phong kham (mau Hybrid)

Muc tieu:
- Moi may chay app local qua `127.0.0.1` (nhanh, khong phu thuoc IP LAN)
- Dong bo du lieu ve server trung tam bang hostname co dinh (`clinic-sync.local`)

## Bo file da co san

- `deployment/machine-config.example.json`
- `scripts/start_clinic_node.ps1`
- `scripts/setup_machine_network.ps1`
- `SETUP_MACHINE_FIRST_TIME.bat`
- `START_CLINIC_LOCAL.bat`

## A. Cau hinh server trung tam (1 lan)

1. Chon may chu dong bo trung tam (VD: `192.168.1.230`)
2. Dam bao may chu chay backend va sync token dung.
3. Dat ten hostname noi bo co dinh:
   - `clinic-sync.local`

## B. Setup tren tung may tram (1 lan / may)

1. Copy app vao may tram.
2. Tao file `deployment/machine-config.json` tu file mau:
   - copy `deployment/machine-config.example.json` -> `deployment/machine-config.json`
3. Sua cac truong:
   - `machine_name`: ten may
   - `app_port`: de 5000 (hoac khac neu trung port)
   - `sync.remote_url`: `https://clinic-sync.local` (hoac `http://clinic-sync.local:5000`)
   - `sync.peer_appointments_url`: giong `sync.remote_url`
   - `network.server_hostname`: `clinic-sync.local`
   - `network.server_ip`: IP hien tai cua may chu
4. Chay file `SETUP_MACHINE_FIRST_TIME.bat` bang quyen Administrator.
   - Buoc nay ghi vao hosts de hostname khong phu thuoc IP hard-code trong app.

## C. Van hanh hang ngay

1. Nhan vien mo app bang `START_CLINIC_LOCAL.bat`
2. Trinh duyet/Electron mo URL:
   - `http://127.0.0.1:5000/booking.html`
   - `http://127.0.0.1:5000/examination-list.html`
   - `http://127.0.0.1:5000/cervical-examination-analysis.html`

## D. Khi may chu doi IP

Chi can cap nhat file `deployment/machine-config.json` tren tung may:
- sua `network.server_ip`

Sau do chay lai:
- `SETUP_MACHINE_FIRST_TIME.bat`

Khong can sua code app.

## E. Kiem tra nhanh sau trien khai

1. Tren may tram:
   - mo `http://127.0.0.1:5000/healthz` -> phai tra `status: ok`
2. Kiem tra dong bo:
   - tao 1 lich hen o may A
   - may B thay du lieu sau vai giay
3. Kiem tra camera may soi:
   - mo `cervical-examination-analysis.html` tren may cam may soi
   - thu `Chup anh tu may soi`

## F. Goi y dong bo voi Electron

Khi dong goi Electron:
- Electron chi mo `http://127.0.0.1:5000`
- Backend local van doc `deployment/machine-config.json`
- Quy trinh setup/hosts o tren giu nguyen.
