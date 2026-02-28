# 🎯 HUONG DAN CAU HINH VOLUSON E10

## ✅ DA XAC NHAN:
- **Voluson AE Title**: `VOLUSON_E10` ✅
- **IP Address**: `10.17.2.1` ✅
- **Port**: `104` ✅
- **Test Connection**: Ping accepted

## 🔧 VAN DE:
Voluson E10 chua co cau hinh nhan worklist tu he thong phong kham!

## 📋 CAN LAM:

### 1. Them DICOM Destination tren may Voluson:

**Vao menu**: Settings -> Network -> DICOM -> Server Configuration

**Them moi Destination voi thong tin sau:**
- **Services**: 
  - ✅ STORE (check)
  - ✅ WORKLIST (check)
- **Alias**: `CLINIC_PC`
- **AE Title**: `CLINIC_SYSTEM`
- **IP Address**: `10.17.2.2`
- **Port**: `104`
- **Color / Size**: `Color / Original`

### 2. Luu cau hinh va test:

1. Nhan **OK** hoac **Save** de luu
2. Nhan **Test Connection** de test ket noi
3. Kiem tra **Ping** va **Verify** phai la **OK**

### 3. Sau khi cau hinh xong:

He thong phong kham se tu dong gui worklist den may Voluson E10!

## 🎯 SO SANH CAU HINH:

### Hien tai (tren may):
- `DICOM_EXPORT` -> IP: `10.17.2.2`, AE Title: `PC`, Services: STORE ✅
- `ViewPoint WL` -> IP: `10.17.2.1`, AE Title: `VOLUSON_E10`, Services: WORKLIST ❌

### Can them:
- `CLINIC_PC` -> IP: `10.17.2.2`, AE Title: `CLINIC_SYSTEM`, Services: STORE + WORKLIST ✅

## 📸 HINH ANH MINH HOA:

Ban can them mot dong moi trong bang "Configured DICOM Destinations" voi:
- Alias: `CLINIC_PC`
- AE Title: `CLINIC_SYSTEM`
- IP: `10.17.2.2`
- Port: `104`
- Services: STORE (checked) + WORKLIST (checked)

**Sau khi them va luu xong, test lai ket noi!** 🎉
