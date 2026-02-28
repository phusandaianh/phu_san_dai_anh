# 🚀 VOLUSON E10 - QUICK START (1 PAGE REFERENCE)

**Print this page and keep it by the Voluson E10 machine!**

---

## ⚡ 5-MINUTE SETUP

### STEP 1: SERVER (Clinic Computer)
```bash
cd j:\DU_AN_AI\Phong_kham_dai_anh
python mwl_server.py
# Wait for: "INFO: Waiting for connections..."
```

### STEP 2: VOLUSON MENU
```
Setup → DICOM Services → Modality Worklist → Add Server
```

### STEP 3: FILL IN FIELDS
| Field | Value |
|-------|-------|
| Server Name | Phong_Kham_Dai_Anh |
| Server IP | 10.17.2.2 |
| Port | 104 |
| Local AE Title | VOLUSON_E10 |
| Remote AE Title | CLINIC_SYSTEM |

### STEP 4: TEST CONNECTION
```
Click: [Test Connection]
Result: ✅ Connection successful
```

### STEP 5: QUERY PATIENTS
```
New Exam → Query Worklist → [Search]
Select patient → [Load]
```

**Done! Now scan and save.** ✅

---

## 🔧 SETTINGS AT A GLANCE

```
┌──────────────────────────────┐
│ DICOM Worklist Server Config │
├──────────────────────────────┤
│ Server:      Phong_Kham_Dai_An│
│ IP:          10.17.2.2       │
│ Port:        104             │
│ Local AE:    VOLUSON_E10     │
│ Remote AE:   CLINIC_SYSTEM   │
│ Type:        Modality WL     │
└──────────────────────────────┘
```

---

## ⚠️ QUICK TROUBLESHOOTING

| Problem | Fix |
|---------|-----|
| ❌ Connection Failed | Restart server: `python mwl_server.py` |
| ❌ No Patients | Wait 5 min, click Refresh |
| ⏳ Slow | Restart Voluson |
| ❓ IP Wrong | Get server IP: `ipconfig` |
| 🔴 No Network | Check cable, ping `10.17.2.2` |

---

## 📞 HELP

**Server not running?**
```
Check: netstat -ano | findstr :104
Fix: python mwl_server.py
```

**Need patient added?**
Contact clinic reception to add appointment

**Emergency?**
Call clinic IT: [PHONE]

---

## ✅ DAILY CHECKLIST

```
Morning:
☐ Server running on clinic computer
☐ Voluson powered on
☐ Test Connection = ✅
☐ Can see patients in Worklist

Throughout day:
☐ Query patients before scan
☐ Save results after scan
☐ Report any issues to IT

Evening:
☐ Shutdown Voluson properly
☐ Leave server running (auto-sync)
☐ Check for error messages
```

---

## 🎯 WORKFLOW

```
1. PATIENT ARRIVES
   ↓
2. SELECT: New Exam → Query Worklist
   ↓
3. SEARCH: [Search button]
   ↓
4. LOAD: Patient info → [Load]
   ↓
5. SCAN: Perform ultrasound
   ↓
6. SAVE: Save results → [Save]
   ↓
7. DONE: Results in system ✅
```

---

## 🔑 KEY NUMBERS

| Item | Value |
|------|-------|
| Server IP | 10.17.2.2 |
| Server Port | 104 |
| Voluson IP | 10.17.2.1 |
| Local AE Title | VOLUSON_E10 |
| Remote AE Title | CLINIC_SYSTEM |

---

## 📝 NOTES

```
Last configured: 2025-11-11
By: Clinic IT
Version: 1.0
Status: Ready

If problems:
1. Note the error message
2. Take screenshot
3. Contact IT with details
```

---

**Version 1.0** | **11-Nov-2025** | **Status: ✅ READY**

*Laminate this page and attach to Voluson E10!*
