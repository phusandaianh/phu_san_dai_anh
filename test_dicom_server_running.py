#!/usr/bin/env python3
"""
Test if DICOM server is running
"""

import socket
import time

def test_dicom_server(host='localhost', port=104, timeout=5):
    """Test if DICOM server is listening on port 104"""
    print(f"Testing DICOM server on {host}:{port}...")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print("OK: DICOM server is listening on port 104")
            return True
        else:
            print("FAIL: DICOM server is not listening")
            return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Test DICOM Server")
    print("=" * 60)
    
    # Wait a bit for server to start
    print("\nWaiting for server to start...")
    time.sleep(2)
    
    if test_dicom_server():
        print("\nServer is running! Now test on Voluson machine.")
    else:
        print("\nServer is not running yet. Please check dicom_server.py")
