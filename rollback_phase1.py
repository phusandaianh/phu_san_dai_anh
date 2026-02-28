#!/usr/bin/env python3
"""
Script rollback Phase 1 deployment
Khôi phục hệ thống về trạng thái trước khi triển khai bảo mật
"""

import os
import sys
import shutil
import json
from datetime import datetime

class Phase1Rollback:
    """Phase 1 Rollback System"""
    
    def __init__(self):
        self.backup_dirs = []
        self.latest_backup = None
        
    def log(self, message, level="INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] {level}: {message}")
    
    def find_backups(self):
        """Find available backups"""
        self.log("🔍 Looking for backup directories...")
        
        # Find all backup directories
        for item in os.listdir('.'):
            if item.startswith('backup_') and os.path.isdir(item):
                self.backup_dirs.append(item)
        
        if not self.backup_dirs:
            self.log("❌ No backup directories found!")
            return False
        
        # Sort by timestamp (newest first)
        self.backup_dirs.sort(reverse=True)
        self.latest_backup = self.backup_dirs[0]
        
        self.log(f"✅ Found {len(self.backup_dirs)} backup(s)")
        self.log(f"📁 Latest backup: {self.latest_backup}")
        
        return True
    
    def verify_backup(self, backup_dir):
        """Verify backup integrity"""
        self.log(f"🔍 Verifying backup: {backup_dir}")
        
        required_files = ['clinic.db', 'app.py', 'requirements.txt']
        missing_files = []
        
        for file in required_files:
            if not os.path.exists(f"{backup_dir}/{file}"):
                missing_files.append(file)
        
        if missing_files:
            self.log(f"❌ Missing files in backup: {missing_files}")
            return False
        
        # Check backup info
        backup_info_file = f"{backup_dir}/backup_info.json"
        if os.path.exists(backup_info_file):
            try:
                with open(backup_info_file, 'r') as f:
                    backup_info = json.load(f)
                self.log(f"✅ Backup info: {backup_info.get('description', 'Unknown')}")
            except:
                self.log("⚠️  Could not read backup info")
        
        self.log("✅ Backup verification completed")
        return True
    
    def rollback_database(self, backup_dir):
        """Rollback database"""
        self.log("🔄 Rolling back database...")
        
        try:
            # Backup current database
            if os.path.exists('clinic.db'):
                shutil.copy2('clinic.db', f'clinic_rollback_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db')
                self.log("✅ Current database backed up")
            
            # Restore from backup
            shutil.copy2(f'{backup_dir}/clinic.db', 'clinic.db')
            self.log("✅ Database restored from backup")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Database rollback failed: {str(e)}")
            return False
    
    def rollback_files(self, backup_dir):
        """Rollback configuration files"""
        self.log("🔄 Rolling back configuration files...")
        
        files_to_restore = ['app.py', 'requirements.txt', 'voluson_config.json']
        
        for file in files_to_restore:
            if os.path.exists(f'{backup_dir}/{file}'):
                try:
                    # Backup current file
                    if os.path.exists(file):
                        shutil.copy2(file, f'{file}.rollback_backup')
                    
                    # Restore from backup
                    shutil.copy2(f'{backup_dir}/{file}', file)
                    self.log(f"✅ {file} restored")
                    
                except Exception as e:
                    self.log(f"❌ Failed to restore {file}: {str(e)}")
                    return False
            else:
                self.log(f"⚠️  {file} not found in backup")
        
        return True
    
    def remove_security_files(self):
        """Remove security-related files"""
        self.log("🗑️  Removing security files...")
        
        security_files = [
            'security_enhancements.py',
            'secure_auth_system.py', 
            'security_middleware.py',
            'security_test_suite.py',
            'security.log',
            'phase1_deployment_report.json',
            'security_test_report.json'
        ]
        
        removed_count = 0
        for file in security_files:
            if os.path.exists(file):
                try:
                    os.remove(file)
                    self.log(f"✅ Removed {file}")
                    removed_count += 1
                except Exception as e:
                    self.log(f"❌ Failed to remove {file}: {str(e)}")
        
        self.log(f"✅ Removed {removed_count} security files")
        return True
    
    def clean_dependencies(self):
        """Remove security dependencies"""
        self.log("🧹 Cleaning security dependencies...")
        
        security_packages = [
            'bcrypt',
            'cryptography', 
            'flask-jwt-extended',
            'flask-talisman'
        ]
        
        for package in security_packages:
            try:
                import subprocess
                result = subprocess.run(['pip', 'uninstall', package, '-y'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    self.log(f"✅ Uninstalled {package}")
                else:
                    self.log(f"⚠️  Could not uninstall {package}")
            except Exception as e:
                self.log(f"❌ Error uninstalling {package}: {str(e)}")
        
        return True
    
    def verify_rollback(self):
        """Verify rollback was successful"""
        self.log("🔍 Verifying rollback...")
        
        # Check if original files exist
        original_files = ['app.py', 'clinic.db']
        for file in original_files:
            if not os.path.exists(file):
                self.log(f"❌ {file} missing after rollback!")
                return False
        
        # Check if security files are removed
        security_files = ['security_enhancements.py', 'secure_auth_system.py']
        for file in security_files:
            if os.path.exists(file):
                self.log(f"⚠️  {file} still exists")
        
        self.log("✅ Rollback verification completed")
        return True
    
    def create_rollback_report(self):
        """Create rollback report"""
        self.log("📊 Creating rollback report...")
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'action': 'Phase 1 Rollback',
            'backup_used': self.latest_backup,
            'files_restored': ['clinic.db', 'app.py', 'requirements.txt'],
            'security_files_removed': True,
            'status': 'COMPLETED'
        }
        
        with open('rollback_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        self.log("✅ Rollback report saved: rollback_report.json")
        return True
    
    def rollback(self):
        """Main rollback function"""
        self.log("🔄 Starting Phase 1 Rollback")
        self.log("=" * 60)
        
        # Find backups
        if not self.find_backups():
            return False
        
        # Verify latest backup
        if not self.verify_backup(self.latest_backup):
            self.log("❌ Latest backup is corrupted!")
            return False
        
        # Confirm rollback
        print(f"\n⚠️  WARNING: This will restore from backup: {self.latest_backup}")
        print("📋 This will remove all security features!")
        
        confirm = input("\n🤔 Do you want to continue with rollback? (yes/no): ").lower()
        if confirm not in ['yes', 'y']:
            self.log("❌ Rollback cancelled")
            return False
        
        # Perform rollback
        steps = [
            ("Rollback Database", lambda: self.rollback_database(self.latest_backup)),
            ("Rollback Files", lambda: self.rollback_files(self.latest_backup)),
            ("Remove Security Files", self.remove_security_files),
            ("Clean Dependencies", self.clean_dependencies),
            ("Verify Rollback", self.verify_rollback),
            ("Create Report", self.create_rollback_report)
        ]
        
        for step_name, step_func in steps:
            self.log(f"\n📋 {step_name}...")
            if not step_func():
                self.log(f"❌ {step_name} failed!")
                return False
            else:
                self.log(f"✅ {step_name} completed")
        
        # Final report
        self.log("\n" + "=" * 60)
        self.log("📊 ROLLBACK SUMMARY")
        self.log("=" * 60)
        self.log("🎉 PHASE 1 ROLLBACK SUCCESSFUL!")
        self.log("🔄 System restored to pre-security state")
        self.log("📊 Check rollback_report.json for details")
        
        return True

def main():
    """Main function"""
    print("=" * 60)
    print("    PHASE 1 ROLLBACK SYSTEM")
    print("    Phong kham chuyen khoa Phu San Dai Anh")
    print("=" * 60)
    
    # Check if running in correct directory
    if not os.path.exists('app.py'):
        print("❌ Error: app.py not found. Please run from project root directory.")
        sys.exit(1)
    
    # Start rollback
    rollback = Phase1Rollback()
    success = rollback.rollback()
    
    if success:
        print("\n🎉 Rollback completed successfully!")
        print("🔄 System restored to pre-security state")
        print("📋 Next steps:")
        print("   1. Test system functionality")
        print("   2. Check if everything works as before")
        print("   3. Consider re-deploying security later")
        sys.exit(0)
    else:
        print("\n❌ Rollback failed!")
        print("🔄 Manual intervention may be required")
        print("📞 Contact support if issues persist")
        sys.exit(1)

if __name__ == "__main__":
    main()
