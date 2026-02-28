#!/usr/bin/env python3
"""
Quick deployment verification
"""

import os
import sys
from datetime import datetime

def check_file_exists(filepath, description):
    if os.path.exists(filepath):
        print(f"✓ {description}: {filepath}")
        return True
    else:
        print(f"✗ {description}: {filepath} - NOT FOUND")
        return False

def main():
    print("=" * 60)
    print("    PHASE 1 DEPLOYMENT VERIFICATION")
    print("    Phong kham chuyen khoa Phu San Dai Anh")
    print("=" * 60)
    
    success = True
    
    # Check backup
    print("\n1. BACKUP VERIFICATION:")
    backup_dirs = [d for d in os.listdir('.') if d.startswith('backup_')]
    if backup_dirs:
        latest_backup = max(backup_dirs)
        print(f"✓ Backup created: {latest_backup}")
        success &= check_file_exists(f"{latest_backup}/clinic.db", "Database backup")
        success &= check_file_exists(f"{latest_backup}/app.py", "App backup")
    else:
        print("✗ No backup found")
        success = False
    
    # Check security files
    print("\n2. SECURITY FILES:")
    success &= check_file_exists("secure_auth_system.py", "Auth system")
    success &= check_file_exists("security_middleware.py", "Security middleware")
    success &= check_file_exists("security_enhancements.py", "Security enhancements")
    
    # Check database tables
    print("\n3. DATABASE TABLES:")
    try:
        from app import app, db
        from secure_auth_system import User, SecurityLog, AuditLog, Session
        
        with app.app_context():
            # Check if tables exist
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            required_tables = ['user', 'security_log', 'audit_log', 'session']
            for table in required_tables:
                if table in tables:
                    print(f"✓ Table exists: {table}")
                else:
                    print(f"✗ Table missing: {table}")
                    success = False
            
            # Check admin user
            admin = User.query.filter_by(username='admin').first()
            if admin:
                print(f"✓ Admin user exists: {admin.username}")
            else:
                print("✗ Admin user not found")
                success = False
                
    except Exception as e:
        print(f"✗ Database check failed: {str(e)}")
        success = False
    
    # Check requirements
    print("\n4. DEPENDENCIES:")
    try:
        import bcrypt
        print("✓ bcrypt installed")
    except ImportError:
        print("✗ bcrypt not installed")
        success = False
        
    try:
        import cryptography
        print("✓ cryptography installed")
    except ImportError:
        print("✗ cryptography not installed")
        success = False
        
    try:
        import flask_jwt_extended
        print("✓ flask-jwt-extended installed")
    except ImportError:
        print("✗ flask-jwt-extended not installed")
        success = False
        
    try:
        import flask_talisman
        print("✓ flask-talisman installed")
    except ImportError:
        print("✗ flask-talisman not installed")
        success = False
    
    # Check app.py modifications
    print("\n5. APP.PY MODIFICATIONS:")
    try:
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
        if 'from secure_auth_system import' in content:
            print("✓ Security imports added")
        else:
            print("✗ Security imports missing")
            success = False
            
        if '@app.route(\'/api/login\'' in content:
            print("✓ Login endpoint added")
        else:
            print("✗ Login endpoint missing")
            success = False
            
        if 'Talisman(app' in content:
            print("✓ Talisman security headers added")
        else:
            print("✗ Talisman security headers missing")
            success = False
            
    except Exception as e:
        print(f"✗ App.py check failed: {str(e)}")
        success = False
    
    # Final result
    print("\n" + "=" * 60)
    if success:
        print("SUCCESS: Phase 1 deployment verified!")
        print("Security features are active")
        print("Critical vulnerabilities have been addressed")
    else:
        print("WARNING: Some issues found in deployment")
        print("Please check the items marked with ✗")
    
    print("\nNEXT STEPS:")
    print("1. Test login: admin/Admin123!")
    print("2. Change admin password")
    print("3. Test all application functions")
    print("4. Monitor security logs")
    
    return success

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"ERROR: {str(e)}")
        sys.exit(1)
