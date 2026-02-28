# 🚀 QUICK START GUIDE - Run MWL Service

## ⚡ Fastest Way to Start

### For Testing (Development Mode)
```powershell
cd j:\DU_AN_AI\Phong_kham_dai_anh
python app.py
```
- Open browser: http://localhost:5000
- MWL Server auto-starts
- Press Ctrl+C to stop

### For Production (Windows Service - Recommended)
```powershell
# Right-click PowerShell → Run as Administrator
cd j:\DU_AN_AI\Phong_kham_dai_anh
.\run_setup.bat
```
Then:
- Service starts automatically
- Restarts on reboot
- Runs in background 24/7
- Check services: `services.msc`

---

## 📋 What's Running

| Component | What it does | How to verify |
|-----------|-------------|---|
| **Flask App** | Web interface, REST APIs | Open http://localhost:5000 |
| **MWL Server** | DICOM Worklist on port 104 | `netstat -ano \| findstr :104` |
| **Auto-sync** | Syncs appointments every 5 min | Check `mwl_server.log` |

---

## ✅ Check System Status

### Is Flask app running?
```powershell
netstat -ano | findstr :5000
```
Should show: `LISTENING` with some PID

### Is MWL Server running?
```powershell
netstat -ano | findstr :104
```
Should show: `LISTENING` with port 104

### View MWL Server logs
```powershell
Get-Content mwl_server.log -Tail 20
```

---

## 🎮 Admin Panel Features

### Location
http://localhost:5000/admin.html

### New Button: "Đồng bộ Worklist"
- **What it does:** Immediately syncs all appointments with ultrasound service to DICOM worklist
- **Who can use it:** Users with `manage_worklist` permission
- **Result:** Shows how many entries were synced

### Automatic Sync
- Runs every 5 minutes automatically
- No action needed - fully background
- Check logs to verify it's working

---

## 🩺 Testing MWL with Voluson E10

### Prerequisites
- Voluson IP: 10.17.2.1
- Server IP: 10.17.2.2 (or your clinic server IP)
- Network cable connected between devices
- MWL Server running (port 104)

### Steps
1. On Voluson, go to: **Setup → Network → DICOM Services**
2. Configure:
   - Server IP: 10.17.2.2
   - Port: 104
   - AE Title: CLINIC_SYSTEM
3. Click **Test Connection**
   - Should say: "Connection successful"
4. In Worklist tab:
   - Should show patient list from clinic.db
   - Each appointment = 1 worklist entry

---

## 📊 Monitoring

### Real-time logs
```powershell
Get-Content mwl_server.log -Wait
```
(Press Ctrl+C to stop)

### Check synced patients
```powershell
python -c "import mwl_store; import json; 
mwl_store.init_db()
for entry in mwl_store.get_all_entries():
    print(entry)"
```

### View worklist file
```powershell
Get-Content worklist.json | ConvertFrom-Json | Format-Table
```

---

## 🐛 If Something Goes Wrong

### MWL Server won't start
```powershell
# Check if port 104 is already in use
netstat -ano | findstr :104

# If occupied, find process:
Get-Process -Id <PID from netstat>

# Kill it if needed:
Stop-Process -Id <PID> -Force
```

### Flask app won't start
```powershell
# Check if port 5000 in use
netstat -ano | findstr :5000

# Clear Python cache
Remove-Item -Recurse -Force .\__pycache__
python app.py
```

### No worklist entries on Voluson
1. Verify appointments exist: http://localhost:5000/examination-list.html
2. Check appointment has "siêu âm" service type
3. Run manual sync: POST to http://localhost:5000/api/mwl-sync
4. Check logs: `Get-Content mwl_server.log -Tail 50`

---

## 🔧 Service Management

### See Windows Service status
```powershell
Get-Service | Where-Object {$_.Name -like "*MWL*"}
```

### Start service
```powershell
Start-Service -Name "PK_DaiAnh_MWL"
```

### Stop service
```powershell
Stop-Service -Name "PK_DaiAnh_MWL"
```

### Restart service
```powershell
Restart-Service -Name "PK_DaiAnh_MWL"
```

### Remove service (if needed)
```powershell
# Run as Administrator
sc delete "PK_DaiAnh_MWL"
```

---

## 📞 Key Contacts

**Config File Issues:** Check `clinic.db` location
**Port Conflicts:** Use `netstat` to find what's using ports 5000, 104
**DICOM Issues:** Verify Voluson AE Title = CLINIC_SYSTEM
**Database Issues:** Backup `clinic.db` and `mwl.db` before troubleshooting

---

**Status:** 🟢 All Systems Go!  
**Last Updated:** 11-Nov-2025
