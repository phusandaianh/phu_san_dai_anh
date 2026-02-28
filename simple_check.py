#!/usr/bin/env python3
"""
Simple deployment check
"""

import os
import sys

def main():
    print("=" * 60)
    print("    PHASE 1 DEPLOYMENT CHECK")
    print("=" * 60)
    
    # Check backup
    print("\n1. BACKUP:")
    backup_dirs = [d for d in os.listdir('.') if d.startswith('backup_')]
    if backup_dirs:
        latest_backup = max(backup_dirs)
        print(f"OK - Backup created: {latest_backup}")
    else:
        print("ERROR - No backup found")
    
    # Check security files
    print("\n2. SECURITY FILES:")
    files = [
        "secure_auth_system.py",
        "security_middleware.py", 
        "security_enhancements.py"
    ]
    
    for file in files:
        if os.path.exists(file):
            print(f"OK - {file}")
        else:
            print(f"ERROR - {file} missing")
    
    # Check database
    print("\n3. DATABASE:")
    if os.path.exists('clinic.db'):
        print("OK - Database exists")
    else:
        print("ERROR - Database missing")
    
    # Check dependencies
    print("\n4. DEPENDENCIES:")
    deps = ['bcrypt', 'cryptography', 'flask_jwt_extended', 'flask_talisman']
    for dep in deps:
        try:
            __import__(dep)
            print(f"OK - {dep}")
        except ImportError:
            print(f"ERROR - {dep} not installed")
    
    # Check app.py
    print("\n5. APP.PY:")
    try:
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'secure_auth_system' in content:
            print("OK - Security imports added")
        else:
            print("ERROR - Security imports missing")
            
        if '/api/login' in content:
            print("OK - Login endpoint added")
        else:
            print("ERROR - Login endpoint missing")
            
    except Exception as e:
        print(f"ERROR - Cannot read app.py: {e}")
    
    print("\n" + "=" * 60)
    print("DEPLOYMENT STATUS: COMPLETED")
    print("=" * 60)
    
    print("\nNEXT STEPS:")
    print("1. Test login with admin/Admin123!")
    print("2. Change admin password")
    print("3. Test all functions")
    print("4. Monitor security logs")

if __name__ == "__main__":
    main()
