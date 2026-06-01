# Quy trinh cap nhat 1-click (LAN)

Tai lieu nay mo ta cach phat hanh va cap nhat app cho cac may trong phong kham voi server noi bo.

## 1) Kien truc

- **Server phat hanh noi bo**: luu `latest.json` + file zip release.
- **May phat hanh (admin/dev)**: build va publish ban moi.
- **May client**: chay script update 1-click de tai va cap nhat.

## 2) Chuan bi 1 lan

1. Tao file cau hinh:
   - Copy `update/update-config.example.json` thanh `update/update-config.json`
   - Sua:
     - `public_base_url`: URL HTTP noi bo de client tai update
     - `publish_share`: share path de publish file (`\\server\share`)
     - `client_app_root`: thu muc app tren may client
2. Tao web root update tren server noi bo (IIS/Nginx/file server HTTP), vi du:
   - `http://192.168.1.230:8080/updates`
3. Dam bao `publish_share` trung voi thu muc web root hoac duoc dong bo vao web root.

## 3) Release ban moi (admin)

Tu root project:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_release.ps1 -Version 2026.04.27.1
powershell -ExecutionPolicy Bypass -File .\scripts\publish_release.ps1 -Version 2026.04.27.1
```

Ket qua:
- `releases/clinic-app-2026.04.27.1.zip`
- tren server update co:
  - `clinic-app-2026.04.27.1.zip`
  - `latest.json` (tro den ban moi nhat)

## 4) Update 1-click tren may client

Tu thu muc app client:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\update_client.ps1
```

Script se:
- Doc `latest.json` tu server LAN
- Neu co ban moi: tai zip, verify sha256, backup code cu, copy de cap nhat
- Giu nguyen du lieu van hanh (`clinic.db`, `mwl.db`, `uploads`, `ssl`)

## 5) Rollback nhanh

Backup duoc luu tai:
- `C:\ProgramData\PhongKhamDaiAnh\updater\backup_yyyymmdd_hhmmss`

Neu can rollback:
- Copy nguoc file tu backup ve thu muc app.

## 6) Khuyen nghi van hanh

- Moi lan release tang version theo ngay-gio de de truy vet.
- Chi release khi da test tren 1 may thu nghiem.
- Neu co nhieu may, tao 1 file `.bat` tren desktop:

```bat
@echo off
powershell -ExecutionPolicy Bypass -File "D:\phusandaianh\DU_AN_AI\Phong_kham_dai_anh\scripts\update_client.ps1"
pause
```

Nhan vien chi can bam 1 lan de cap nhat.
