# 🎬 VOLUSON E10 SETUP - VIDEO SCRIPT & QUICK REFERENCE

**Duration:** ~15 minutes  
**Audience:** Ultrasound technicians, clinic staff  
**Goal:** Setup DICOM Worklist on Voluson E10

---

## 📺 SCRIPT DEMO (Step-by-step)

### Scene 1: Server Setup (2 min)

**Narrator:** "First, we need to start the Worklist server on the clinic computer..."

**On Screen:**
```
Step 1: Open Command Prompt
cd j:\DU_AN_AI\Phong_kham_dai_anh

Step 2: Start MWL Server
python mwl_server.py

Expected output:
  INFO: Starting MWL SCP on port 104
  INFO: AE Title: CLINIC_SYSTEM
  INFO: Waiting for connections...
```

**Narrator:** "The server is now listening on port 104 and waiting for connections from ultrasound machines."

---

### Scene 2: Network Check (1 min)

**Narrator:** "Before connecting the Voluson, let's verify the network..."

**On Screen:**
```
Step 1: Check server is running
netstat -ano | findstr :104

Output should show:
  TCP  0.0.0.0:104  0.0.0.0:0  LISTENING

Step 2: From Voluson machine, ping server
ping 10.17.2.2

Output should show:
  Reply from 10.17.2.2: bytes=32 time<1ms TTL=64
```

**Narrator:** "Network connectivity confirmed. Now let's configure the Voluson E10."

---

### Scene 3: Voluson E10 Configuration (5 min)

**Narrator:** "On the Voluson ultrasound machine, we need to add the Worklist server..."

**On Screen (Voluson E10 Display):**
```
Main Menu
  ├─ New Patient
  ├─ Patient List
  ├─ Setup
  │  ├─ System Configuration
  │  ├─ Network
  │  └─ DICOM Services ← Click here
  └─ Help
```

**Narrator:** "Navigate to Setup → DICOM Services"

**On Screen continues:**
```
DICOM Services
  ├─ DICOM Query/Retrieve
  ├─ Modality Worklist ← Select this
  ├─ DICOM Storage
  └─ DICOM Printing

Click: Modality Worklist
```

**On Screen:**
```
Modality Worklist Servers
  ├─ Add New Server...  ← Click here
  ├─ Edit Server
  └─ Delete Server

After clicking "Add New Server":
```

**On Screen - Configuration Dialog:**
```
DICOM Worklist Server Configuration
┌─────────────────────────────────────────────────┐
│ Server Name:        Phong_Kham_Dai_Anh         │
│ Server IP:          10.17.2.2                   │
│ Port:               104                         │
│ Local AE Title:     VOLUSON_E10                 │
│ Remote AE Title:    CLINIC_SYSTEM               │
│ Modality:           US (Ultrasound)             │
│ Service Type:       Modality Worklist           │
│                                                 │
│ [Save] [Test] [Cancel]                         │
└─────────────────────────────────────────────────┘
```

**Narrator:** "Enter the configuration details exactly as shown. These settings tell the Voluson how to find our clinic server."

**Steps highlighted:**
- 🔴 Server Name: Type "Phong_Kham_Dai_Anh"
- 🔴 Server IP: Type "10.17.2.2"
- 🔴 Port: Type "104"
- 🔴 Local AE Title: Type "VOLUSON_E10"
- 🔴 Remote AE Title: Type "CLINIC_SYSTEM"

**Narrator:** "After entering all settings, click Save."

---

### Scene 4: Connection Test (2 min)

**Narrator:** "Let's test if the Voluson can connect to our Worklist server..."

**On Screen (Voluson):**
```
DICOM Worklist Servers
  ├─ Phong_Kham_Dai_Anh ← Select
  │  └─ [Edit] [Test] [Delete]
  └─ Test Connection...

Click: [Test]

Status messages:
  ⏳ Connecting...
  ⏳ Verifying...
  ✅ Connection successful!
  ✅ Server responding
  ✅ Worklist available
```

**Narrator:** "Success! The Voluson is now connected to our Worklist server. You should see confirmation on the screen."

**On Screen (Server):**
```
Server logs show:
  INFO: Request from VOLUSON_E10
  INFO: C-FIND request received
  INFO: Query worklist entries
  INFO: Sending 2 entries
  INFO: C-FIND response sent
```

**Narrator:** "On the server side, we can see the successful connection in the logs."

---

### Scene 5: Query Worklist (3 min)

**Narrator:** "Now let's see how to retrieve patient information from the Worklist..."

**On Screen (Voluson - Main Menu):**
```
When starting a new exam:
  New Exam
    ├─ Manual Entry
    └─ Query Worklist ← Select this
```

**On Screen (Voluson - Query Screen):**
```
Query Modality Worklist
┌─────────────────────────────┐
│ Server: Phong_Kham_Dai_Anh │
│ Patient Name: [      ]      │ (optional)
│ Patient ID:   [      ]      │ (optional)
│ Modality:     US            │
│                             │
│ [Search] [Cancel]           │
└─────────────────────────────┘
```

**Narrator:** "You can leave these fields empty to get all patients, or enter specific criteria. Let's search for all ultrasound patients."

**On Screen - Results:**
```
Query Results
┌───────────────────────────────────────┐
│ Patient Name     | Patient ID | Date  │
├───────────────────────────────────────┤
│ Nguyễn Thị Test  │ 1          | 11/11 │
│ Hà Ngọc Đại      │ 1          | 11/09 │
└───────────────────────────────────────┘

[Load] [Refresh] [Cancel]
```

**Narrator:** "The Worklist shows two patients with ultrasound appointments. Let's select the first one and load the information."

**On Screen - After clicking Load:**
```
Patient Information Loaded:
  Name:        Nguyễn Thị Test
  ID:          1
  Age/DOB:     [calculated]
  Exam Type:   Siêu âm thai (Obstetric Ultrasound)
  Scheduled:   2025-11-11 14:30:00
  Accession #: ACC000015
  
Status: ✅ Ready to scan
```

**Narrator:** "Perfect! Patient information is loaded and ready for the ultrasound examination."

---

### Scene 6: During Exam (2 min)

**Narrator:** "Now the patient is on the table, and we're performing the ultrasound scan..."

**On Screen (Voluson Display):**
```
Patient: Nguyễn Thị Test
Study:   Obstetric Ultrasound
┌─────────────────────────────────────┐
│                                     │
│        [Ultrasound B-mode image]    │
│                                     │
│ Measurements: 20.5 cm              │
│ Notes: Normal development           │
└─────────────────────────────────────┘

[Save] [Measure] [Capture] [Report]
```

**Narrator:** "During the scan, you take measurements, capture images, and add clinical notes. All data is associated with this patient automatically."

---

### Scene 7: Save Results (2 min)

**Narrator:** "After completing the scan, we save the results..."

**On Screen (Voluson - Save Dialog):**
```
Save Exam Results

Patient: Nguyễn Thị Test
Study:   Obstetric Ultrasound

Options:
  ☑ Save to local drive
  ☐ Send to PACS
  ☐ Send to DICOM Server
  ☑ Generate PDF report

[Save] [Cancel]
```

**Narrator:** "Select your save options. We can save locally, export to PACS, or generate a PDF report for the patient."

---

### Scene 8: Verification (1 min)

**Narrator:** "Finally, let's verify the data is recorded in the clinic system..."

**On Screen (Clinic Web Interface):**
```
Access: http://clinic-server:5000/admin.html

Ultrasound Results
├─ Nguyễn Thị Test (11/11/2025)
│  ├─ Status: Complete
│  ├─ Images: 12 captured
│  ├─ Report: Generated
│  └─ Measurements: Saved
└─ More results...
```

**Narrator:** "The exam results are automatically recorded in the clinic's Worklist system. Doctors can review everything later."

---

## 🎯 QUICK REFERENCE CARD

**Print this and keep by Voluson E10:**

```
╔════════════════════════════════════════════════════╗
║   VOLUSON E10 - DICOM WORKLIST QUICK REFERENCE   ║
╚════════════════════════════════════════════════════╝

STARTUP:
1. Server: python mwl_server.py (on clinic computer)
2. Voluson: Power on, wait for system ready

CONFIGURATION (ONE-TIME):
1. Voluson Menu → Setup → DICOM Services
2. → Modality Worklist → Add New Server
3. Enter:
   • Server Name: Phong_Kham_Dai_Anh
   • IP: 10.17.2.2
   • Port: 104
   • Local AE: VOLUSON_E10
   • Remote AE: CLINIC_SYSTEM
4. Save and Test Connection

DAILY USE:
1. New Exam → Query Worklist
2. Choose patient from list
3. Load information
4. Perform scan
5. Save results

TROUBLESHOOTING:
Connection Failed:
  → Check if server is running
  → Check network cable
  → Verify IP address (10.17.2.2)
  
No Patients:
  → Check if appointments exist
  → Wait 5 minutes for auto-sync
  → Try "Refresh" in Worklist query

Contact: Clinic Admin / IT Support
Emergency: +84 (clinic phone number)

Last Updated: 2025-11-11
Version: 1.0
```

---

## 🎓 TRAINING SLIDES

### Slide 1: What is DICOM Worklist?
```
DICOM Worklist allows:
  ✓ Automatic patient data retrieval
  ✓ Reduced manual data entry
  ✓ Fewer transcription errors
  ✓ Better workflow efficiency
  
Benefits:
  • Save time (5-10 min per patient)
  • Reduce errors
  • Automatic data backup
```

### Slide 2: System Architecture
```
[Clinic Database]
       ↓ (Appointments)
   [Worklist Server]
       ↓ (DICOM Queries)
  [Voluson E10]
       ↓ (Ultrasound)
  [DICOM Images + Report]
       ↓
[Clinic Archive]
```

### Slide 3: Day-in-the-Life Example
```
8:00 AM - Receptionist books appointment
  → Enters: Patient name, DOB, Exam type
  → Saves to system
  
8:30 AM - Auto-sync runs
  → Reads appointments
  → Creates worklist entries
  → Ready for ultrasound machine
  
9:00 AM - Patient arrives
  → Technician queries worklist
  → Loads patient info
  → No manual entry needed!
  
9:30 AM - Ultrasound done
  → Results saved automatically
  → Report generated
  → Data backup complete
```

### Slide 4: Tips & Best Practices
```
DO:
  ✓ Always verify server is running before starting
  ✓ Test connection when configuring
  ✓ Arrive early to let auto-sync run
  ✓ Save results immediately after scan
  ✓ Report issues to IT admin

DON'T:
  ✗ Manually enter patient data (use Worklist)
  ✗ Ignore connection errors
  ✗ Force shut down during query
  ✗ Modify server IP without admin approval
  ✗ Share AE Title credentials
```

---

## 📱 MOBILE REFERENCE

**For phone/tablet quick lookup:**

```
VOLUSON DICOM SETUP CHECKLIST:

☐ Server Running?
  netstat -ano | findstr :104

☐ Network OK?
  ping 10.17.2.2

☐ Voluson Settings:
  • IP: 10.17.2.2
  • Port: 104
  • Local AE: VOLUSON_E10
  • Remote AE: CLINIC_SYSTEM

☐ Test Connection: ✓

☐ Query Worklist: Patient list visible?

☐ Load Patient: Auto-filled?

☐ Save Results: Success?

If anything fails, see TROUBLESHOOTING section
```

---

## 🎥 VIDEO PRODUCTION NOTES

**Equipment needed:**
- Screen recording software (OBS, ScreenFlow)
- Microphone for narration
- Voluson E10 simulator or actual device
- Server console view

**Best practices:**
- Record at 1080p resolution
- Use captions for important steps
- Highlight UI elements
- Add sound effects for key actions
- Include background music (royalty-free)

**Distribution:**
- Upload to clinic staff portal
- Share via email (reference)
- Print quick reference cards
- Conduct live training session

---

## 🏁 SUMMARY

This script provides:
✅ 15-minute training video outline  
✅ Step-by-step UI navigation  
✅ Expected outputs at each stage  
✅ Quick reference card for printing  
✅ Training slides  
✅ Mobile reference guide  

**Total training time needed:**
- Video: 15 minutes
- Hands-on: 15 minutes
- Q&A: 10 minutes
- **Total: ~40 minutes**

---

**Script Version:** 1.0  
**Last Updated:** 11 November 2025  
**Status:** Ready for production
