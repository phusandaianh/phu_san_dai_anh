# Trien khai hang loat tu dong (CSV)

Tai lieu nay dung cho viec day app den nhieu may trong LAN bang 1 lenh.

## 1) Chuan bi danh sach may

1. Copy file:
   - `deployment/machines.example.csv` -> `deployment/machines.csv`
2. Sua thong tin tung may:
   - `machine_name`: ten may
   - `target_path`: duong dan UNC den thu muc cai app tren may do  
     (VD: `\\LETAN01\C$\ClinicApp`)
   - `app_port`: thuong la `5000`
   - `server_hostname`: VD `clinic-sync.local`
   - `server_ip`: IP may chu dong bo hien tai
   - `sync_remote_url`: VD `https://clinic-sync.local`
   - `sync_token`: token dong bo

## 2) Chay deploy hang loat (tren may admin)

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\deploy_bulk.ps1 -CsvPath .\deployment\machines.csv
```

Script se:
- Copy bo app den tung `target_path`
- Tao `deployment/machine-config.json` rieng cho tung may
- Tao file `INSTALL_CLIENT_LOCAL.bat` tren tung may

## 3) Kich hoat tren tung may client (lan dau)

Tren tung may, mo thu muc app va chay:
- `INSTALL_CLIENT_LOCAL.bat` (Run as Administrator)

Buoc nay se:
- cap nhat hosts theo `machine-config.json`
- tao shortcut desktop:
  - `Mo Phong Kham`
  - `Cap nhat Phong Kham`

## 4) Van hanh

- Nhan vien mo app bang shortcut `Mo Phong Kham`
- App chay local qua `127.0.0.1` va dong bo du lieu ve server hostname co dinh

## 5) Chay lai deploy khong copy code

Neu chi muon cap nhat config/install scripts:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\deploy_bulk.ps1 -CsvPath .\deployment\machines.csv -SkipCopy
```
