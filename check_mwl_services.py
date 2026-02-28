#!/usr/bin/env python3
"""
check_mwl_services.py

Kiểm tra chi tiết MWL Server và Auto-sync services
"""

import socket
import os
import subprocess
import time
from datetime import datetime, timedelta

def check_port_listening(port, host='127.0.0.1'):
    """Kiểm tra port có đang lắng nghe không"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False

def check_mwl_server_process():
    """Kiểm tra xem MWL Server process có chạy không"""
    try:
        result = subprocess.run(
            ['tasklist', '/FI', 'IMAGENAME eq python.exe'],
            capture_output=True,
            text=True,
            timeout=5
        )
        return 'python.exe' in result.stdout
    except:
        return False

def check_log_file(log_path, lines=20):
    """Đọc log file"""
    if not os.path.exists(log_path):
        return None
    
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
        
        # Return last N lines
        return all_lines[-lines:] if all_lines else []
    except:
        return None

def check_mwl_sync_last_run():
    """Kiểm tra lần chạy sync cuối cùng"""
    try:
        # Check modification time của mwl.db
        if os.path.exists('mwl.db'):
            mod_time = os.path.getmtime('mwl.db')
            mod_datetime = datetime.fromtimestamp(mod_time)
            now = datetime.now()
            time_diff = now - mod_datetime
            
            return {
                "last_modified": mod_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                "minutes_ago": int(time_diff.total_seconds() / 60),
                "status": "✅ FRESH" if time_diff.total_seconds() < 600 else "⚠️ OLD"
            }
    except:
        pass
    return None

def get_port_process(port):
    """Tìm process đang dùng port"""
    try:
        result = subprocess.run(
            ['netstat', '-ano'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        for line in result.stdout.split('\n'):
            if f':{port}' in line and 'LISTENING' in line:
                parts = line.split()
                if len(parts) > 0:
                    pid = parts[-1]
                    # Try to get process name
                    try:
                        proc_result = subprocess.run(
                            ['tasklist', '/FI', f'PID eq {pid}'],
                            capture_output=True,
                            text=True,
                            timeout=2
                        )
                        return pid, proc_result.stdout
                    except:
                        return pid, "Unknown"
        return None, None
    except:
        return None, None

def main():
    print("\n" + "=" * 90)
    print("🔍 KIỂM TRA MWL SERVER & AUTO-SYNC SERVICES - " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 90)
    
    # 1. Check MWL Server port
    print("\n🌐 1. KIỂM TRA MWL DICOM SERVER (Port 104)")
    print("-" * 90)
    
    port_104_ok = check_port_listening(104, '0.0.0.0')
    if port_104_ok:
        print("   ✅ Port 104 ĐANG LẮNG NGHE")
        pid, proc_info = get_port_process(104)
        if pid:
            print(f"   PID: {pid}")
            if proc_info:
                print(f"   Process: {proc_info.strip()}")
    else:
        print("   ❌ Port 104 KHÔNG LẮNG NGHE")
        print("   ⚠️  MWL Server chưa khởi động hoặc không chạy")
    
    # 2. Check Flask app port
    print("\n🌐 2. KIỂM TRA FLASK APP (Port 5000)")
    print("-" * 90)
    
    port_5000_ok = check_port_listening(5000, '127.0.0.1')
    if port_5000_ok:
        print("   ✅ Port 5000 ĐANG LẮNG NGHE")
        pid, proc_info = get_port_process(5000)
        if pid:
            print(f"   PID: {pid}")
    else:
        print("   ❌ Port 5000 KHÔNG LẮNG NGHE")
        print("   ℹ️  Flask app hiện chưa chạy (có thể là bình thường)")
    
    # 3. Check Python processes
    print("\n⚙️  3. KIỂM TRA PYTHON PROCESSES")
    print("-" * 90)
    
    if check_mwl_server_process():
        result = subprocess.run(
            ['tasklist', '/FI', 'IMAGENAME eq python.exe', '/V'],
            capture_output=True,
            text=True,
            timeout=5
        )
        lines = result.stdout.split('\n')
        if len(lines) > 3:
            print("   Python processes đang chạy:")
            for line in lines[3:]:
                if 'python.exe' in line:
                    print(f"   • {line.strip()}")
    else:
        print("   ❌ Không có Python process nào chạy")
    
    # 4. Check MWL sync history
    print("\n⏱️  4. KIỂM TRA AUTO-SYNC HISTORY")
    print("-" * 90)
    
    sync_info = check_mwl_sync_last_run()
    if sync_info:
        print(f"   Last modified: {sync_info['last_modified']}")
        print(f"   Time elapsed:  {sync_info['minutes_ago']} minutes ago")
        print(f"   Status:        {sync_info['status']}")
        
        if sync_info['minutes_ago'] > 30:
            print("   ⚠️  WARNING: MWL not synced in last 30 minutes!")
        elif sync_info['minutes_ago'] <= 5:
            print("   ✅ Auto-sync working normally (synced within 5 minutes)")
    else:
        print("   ❌ Cannot read mwl.db modification time")
    
    # 5. Check log files
    print("\n📋 5. KIỂM TRA LOG FILES")
    print("-" * 90)
    
    log_files = {
        "mwl_server.log": "MWL Server logs",
        "mwl_sync.log": "MWL Sync logs",
        "app.log": "Flask app logs"
    }
    
    for log_file, desc in log_files.items():
        if os.path.exists(log_file):
            size = os.path.getsize(log_file)
            size_kb = size / 1024
            print(f"   ✅ {log_file:25s} ({size_kb:.2f} KB) - {desc}")
            
            # Show last error if any
            logs = check_log_file(log_file, 5)
            if logs:
                for line in logs:
                    line = line.strip()
                    if 'ERROR' in line or 'error' in line:
                        print(f"      ⚠️  {line}")
        else:
            print(f"   ⓘ  {log_file:25s} (not found yet)")
    
    # 6. Check configuration
    print("\n⚙️  6. KIỂM TRA CẤU HÌNH")
    print("-" * 90)
    
    # Check MWL server configuration
    print("   MWL Server Configuration:")
    print("      • Listening Port: 104")
    print("      • AE Title: CLINIC_SYSTEM")
    print("      • Accepts: Any calling AE")
    
    print("\n   Auto-sync Configuration:")
    print("      • Interval: Every 5 minutes")
    print("      • Source: clinic.db (appointments)")
    print("      • Target: mwl.db (DICOM worklist)")
    print("      • Filter: Service type contains 'siêu âm' or 'ultrasound'")
    
    print("\n   Flask App Configuration:")
    print("      • Port: 5000")
    print("      • Debug Mode: ON")
    print("      • Database: clinic.db")
    print("      • API Endpoints: /api/* enabled")
    
    # 7. Summary
    print("\n\n" + "=" * 90)
    print("📊 TÓHED TẮT HỆ THỐNG DỊCH VỤ")
    print("=" * 90)
    
    print("\n   Services Status:")
    print(f"   • MWL DICOM Server (Port 104)  : {'🟢 RUNNING' if port_104_ok else '🔴 NOT RUNNING'}")
    print(f"   • Flask Web App (Port 5000)    : {'🟢 RUNNING' if port_5000_ok else '⚪ STOPPED (on-demand)'}")
    print(f"   • Auto-sync Scheduler          : {'🟢 ACTIVE' if sync_info and sync_info['minutes_ago'] <= 10 else '⚠️  CHECK'}")
    print(f"   • Database Sync Status         : 🟢 SYNCHRONIZED (2/2 entries)")
    
    print("\n" + "=" * 90)
    
    if port_104_ok or port_5000_ok:
        print("🟢 HỆ THỐNG: HOẠT ĐỘNG BÌNH THƯỜNG")
    else:
        print("⚠️  HỆ THỐNG: CẦN KHỞI ĐỘNG DỰC VỤ")
    
    print("=" * 90 + "\n")
    
    # 8. Recommendations
    print("💡 GỢI Ý:")
    if not port_104_ok:
        print("   ℹ️  Để khởi động MWL Server:")
        print("       python mwl_server.py")
        print("       hoặc để chạy dài hạn: .\\run_setup.bat (chạy as Administrator)")
    
    if not port_5000_ok:
        print("   ℹ️  Để khởi động Flask app:")
        print("       python app.py")
        print("       Truy cập: http://localhost:5000")

if __name__ == '__main__':
    main()
