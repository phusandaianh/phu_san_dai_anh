# 🎯 HUONG DAN CHAY DICOM SERVER

## ⚠️ VAN DE:
- **Verify: Failed** tren may Voluson
- He thong phong kham chua co DICOM server de nhan ket noi

## 🔧 GIAI PHAP:

### Buoc 1: Chay DICOM Server tren may tinh phong kham

**Mo Command Prompt moi** (khong phai terminal dang chay app.py):

```bash
cd J:\DU_AN_AI\Phong_kham_dai_anh
python dicom_server.py
```

### Buoc 2: Kiem tra server dang chay

Ban se thay thong bao:
```
DICOM Server cho he thong phong kham
============================================================
AE Title: CLINIC_SYSTEM
Port: 104
Listening for connections...
============================================================
```

### Buoc 3: Test lai tren may Voluson

- Vao DICOM Configuration
- Nhan **Test Connection**
- **Ping** phai la **OK**
- **Verify** phai la **OK** (thay vi Failed)

### Buoc 4: Sau do test dong bo worklist

Quay lai trang `examination-list.html` va them dich vu sieu am
- Data se tu dong dong bo len may Voluson!

## 🎯 LƯU Y:

- **Phai mo 2 terminal**:
  1. Terminal 1: chay `python app.py` (web server)
  2. Terminal 2: chay `python dicom_server.py` (DICOM server)

**Neu chi chay app.py thi Voluson khong the ket noi!**

## 📋 TONG KET:

```
✅ HE THONG:
   - Web Server: app.py (port 5000)
   - DICOM Server: dicom_server.py (port 104)
   
✅ VOLUSON E10:
   - IP: 10.17.2.1
   - AE Title: VOLUSON_E10
   - Port Passthrough: 104
   
✅ MAY TINH PHONG KHAM:
   - IP: 10.17.2.2
   - AE Title: CLINIC_SYSTEM
   - Port: 104
```

**Chi can chay ca 2 server la xong!** 🎉
