# Windows Sync Checklist (Copy-Paste)

Muc tieu: du lieu benh nhan van luu noi bo, nhung booking online (Render) va booking noi bo duoc hop nhat.

## 1) Dat bien tren Render (online node)

Trong Render Dashboard -> Service -> Environment, them:

- `PUBLIC_BOOKING_URL=https://<app>.onrender.com`
- `SYNC_ROLE=online`
- `SYNC_TOKEN=<chuoi-bi-mat-chung-voi-local>`

Sau do redeploy service.

## 2) Chay local voi sync (cach nhanh nhat)

Mo file `run_local_sync.bat` va sua 2 dong:

- `SYNC_REMOTE_URL=https://your-app.onrender.com`
- `SYNC_TOKEN=REPLACE_WITH_A_STRONG_SHARED_SECRET`

Sau do double-click file `run_local_sync.bat`.

### Chay local HTTPS noi bo (khuyen nghi)

Neu can truy cap an toan hon trong mang noi bo, dung file:

- `run_local_sync_https.bat`

Buoc dung:

1. Mo `run_local_sync_https.bat`.
2. Sua 2 dong:
   - `SYNC_REMOTE_URL=https://your-app.onrender.com`
   - `SYNC_TOKEN=REPLACE_WITH_A_STRONG_SHARED_SECRET`
3. Double-click de chay.

Ghi chu:

- Script se tu tao `ssl\dev.crt` va `ssl\dev.key` neu chua co.
- Trinh duyet co the canh bao chung chi self-signed, can trust `ssl\dev.crt` tren may client trong LAN.

## 3) Link su dung

- Benh nhan online: `https://<app>.onrender.com/booking.html`
- Noi bo: `http://<IP-may-noi-bo>:5000/booking.html?internal=1`
- Noi bo HTTPS: `https://<IP-may-noi-bo>:5000/booking.html?internal=1`

## 4) Kiem tra nhanh sau khi bat sync

1. Dang ky 1 lich tren link online.
2. Vao local `examination-list.html` kiem tra lich vua tao da xuat hien.
3. Dang ky 1 lich tren link noi bo.
4. Kiem tra tren online cung thay lich do.

Neu 2 chieu deu thay, sync dang hoat dong dung.

## 5) Copy-paste lenh (neu muon chay bang terminal thay vi .bat)

### CMD

```bat
set SYNC_ROLE=local
set SYNC_REMOTE_URL=https://your-app.onrender.com
set SYNC_TOKEN=REPLACE_WITH_A_STRONG_SHARED_SECRET
set PORT=5000
python run_waitress.py
```

### PowerShell

```powershell
$env:SYNC_ROLE = "local"
$env:SYNC_REMOTE_URL = "https://your-app.onrender.com"
$env:SYNC_TOKEN = "REPLACE_WITH_A_STRONG_SHARED_SECRET"
$env:PORT = "5000"
python .\run_waitress.py
```

## 6) Luu y quan trong

- `SYNC_TOKEN` phai giong nhau giua Render va local.
- Khong de dau `/` cuoi `SYNC_REMOTE_URL`.
- May local can truy cap internet de goi Render.
- Neu doi token, doi dong thoi ca Render va local.
