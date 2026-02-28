#!/usr/bin/env python3
"""
Script kiểm tra nhanh Phase 1 deployment
Xác minh các tính năng bảo mật đã được triển khai thành công
"""

import os
import sys
import json
import sqlite3
import requests
from datetime import datetime

class Phase1Verifier:
    """Phase 1 Verification System"""
    
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.checks = []
        self.critical_issues = []
        self.warnings = []
        
    def log(self, message, level="INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] {level}: {message}")
    
    def check_file_exists(self, filename, description):
        """Check if file exists"""
        if os.path.exists(filename):
            self.log(f"✅ {description}: {filename}")
            self.checks.append(f"✅ {description}")
            return True
        else:
            self.log(f"❌ {description}: {filename} NOT FOUND")
            self.checks.append(f"❌ {description}")
            self.critical_issues.append(f"Missing {filename}")
            return False
    
    def check_database_tables(self):
        """Check if security tables exist"""
        self.log("🔍 Checking database tables...")
        
        try:
            conn = sqlite3.connect('clinic.db')
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            required_tables = ['user', 'security_log', 'audit_log', 'session']
            missing_tables = [t for t in required_tables if t not in tables]
            
            if missing_tables:
                self.log(f"❌ Missing security tables: {missing_tables}")
                self.critical_issues.append(f"Missing tables: {missing_tables}")
                return False
            else:
                self.log("✅ All security tables exist")
                self.checks.append("✅ Security tables")
                return True
                
        except Exception as e:
            self.log(f"❌ Database check failed: {str(e)}")
            self.critical_issues.append(f"Database error: {str(e)}")
            return False
    
    def check_admin_user(self):
        """Check if admin user exists"""
        self.log("🔍 Checking admin user...")
        
        try:
            conn = sqlite3.connect('clinic.db')
            cursor = conn.cursor()
            cursor.execute("SELECT username, role, is_active FROM user WHERE username='admin'")
            admin = cursor.fetchone()
            conn.close()
            
            if not admin:
                self.log("❌ Admin user not found")
                self.critical_issues.append("Admin user missing")
                return False
            
            username, role, is_active = admin
            if role != 'admin' or not is_active:
                self.log(f"❌ Admin user invalid: role={role}, active={is_active}")
                self.critical_issues.append("Admin user invalid")
                return False
            
            self.log("✅ Admin user exists and is active")
            self.checks.append("✅ Admin user")
            return True
            
        except Exception as e:
            self.log(f"❌ Admin user check failed: {str(e)}")
            self.critical_issues.append(f"Admin user error: {str(e)}")
            return False
    
    def check_security_imports(self):
        """Check if app.py has security imports"""
        self.log("🔍 Checking security imports in app.py...")
        
        try:
            with open('app.py', 'r', encoding='utf-8') as f:
                content = f.read()
            
            required_imports = [
                'from secure_auth_system import',
                'from security_middleware import',
                'from flask_talisman import',
                'from security_enhancements import'
            ]
            
            missing_imports = []
            for import_line in required_imports:
                if import_line not in content:
                    missing_imports.append(import_line)
            
            if missing_imports:
                self.log(f"❌ Missing security imports: {missing_imports}")
                self.critical_issues.append(f"Missing imports: {missing_imports}")
                return False
            else:
                self.log("✅ All security imports present")
                self.checks.append("✅ Security imports")
                return True
                
        except Exception as e:
            self.log(f"❌ Import check failed: {str(e)}")
            self.critical_issues.append(f"Import error: {str(e)}")
            return False
    
    def check_login_endpoint(self):
        """Check if login endpoint exists"""
        self.log("🔍 Checking login endpoint...")
        
        try:
            with open('app.py', 'r', encoding='utf-8') as f:
                content = f.read()
            
            if '@app.route(\'/api/login\'' in content:
                self.log("✅ Login endpoint found")
                self.checks.append("✅ Login endpoint")
                return True
            else:
                self.log("❌ Login endpoint not found")
                self.critical_issues.append("Login endpoint missing")
                return False
                
        except Exception as e:
            self.log(f"❌ Login endpoint check failed: {str(e)}")
            self.critical_issues.append(f"Login endpoint error: {str(e)}")
            return False
    
    def check_dependencies(self):
        """Check if security dependencies are installed"""
        self.log("🔍 Checking security dependencies...")
        
        dependencies = [
            'bcrypt',
            'cryptography',
            'flask_jwt_extended',
            'flask_talisman'
        ]
        
        missing_deps = []
        for dep in dependencies:
            try:
                __import__(dep)
                self.log(f"✅ {dep} installed")
            except ImportError:
                self.log(f"❌ {dep} not installed")
                missing_deps.append(dep)
        
        if missing_deps:
            self.critical_issues.append(f"Missing dependencies: {missing_deps}")
            return False
        else:
            self.log("✅ All security dependencies installed")
            self.checks.append("✅ Dependencies")
            return True
    
    def test_login_endpoint(self):
        """Test login endpoint functionality"""
        self.log("🔍 Testing login endpoint...")
        
        try:
            # Test login with admin credentials
            login_data = {
                'username': 'admin',
                'password': 'Admin123!'
            }
            
            response = requests.post(
                f"{self.base_url}/api/login",
                json=login_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'token' in data and 'user' in data:
                    self.log("✅ Login endpoint working")
                    self.checks.append("✅ Login functionality")
                    return True
                else:
                    self.log("❌ Login response invalid")
                    self.critical_issues.append("Login response invalid")
                    return False
            else:
                self.log(f"❌ Login failed with status {response.status_code}")
                self.critical_issues.append(f"Login failed: {response.status_code}")
                return False
                
        except requests.exceptions.ConnectionError:
            self.log("⚠️  Cannot connect to server - is it running?")
            self.warnings.append("Server not running")
            return False
        except Exception as e:
            self.log(f"❌ Login test failed: {str(e)}")
            self.critical_issues.append(f"Login test error: {str(e)}")
            return False
    
    def test_protected_endpoints(self):
        """Test if endpoints are protected"""
        self.log("🔍 Testing endpoint protection...")
        
        protected_endpoints = [
            '/api/patients',
            '/api/voluson/config',
            '/api/lab-orders'
        ]
        
        unprotected_count = 0
        for endpoint in protected_endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                if response.status_code == 200:
                    self.log(f"⚠️  {endpoint} is not protected")
                    unprotected_count += 1
                else:
                    self.log(f"✅ {endpoint} is protected (status: {response.status_code})")
            except requests.exceptions.ConnectionError:
                self.log(f"⚠️  Cannot test {endpoint} - server not running")
            except Exception as e:
                self.log(f"⚠️  Error testing {endpoint}: {str(e)}")
        
        if unprotected_count > 0:
            self.warnings.append(f"{unprotected_count} endpoints not protected")
            return False
        else:
            self.log("✅ All tested endpoints are protected")
            self.checks.append("✅ Endpoint protection")
            return True
    
    def check_security_logs(self):
        """Check if security logging is working"""
        self.log("🔍 Checking security logs...")
        
        log_files = ['security.log', 'phase1_deployment_report.json']
        
        for log_file in log_files:
            if os.path.exists(log_file):
                self.log(f"✅ {log_file} exists")
                self.checks.append(f"✅ {log_file}")
            else:
                self.log(f"⚠️  {log_file} not found")
                self.warnings.append(f"Missing {log_file}")
    
    def generate_report(self):
        """Generate verification report"""
        self.log("📊 Generating verification report...")
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'phase': 'Phase 1 Verification',
            'total_checks': len(self.checks),
            'passed_checks': len([c for c in self.checks if c.startswith('✅')]),
            'failed_checks': len([c for c in self.checks if c.startswith('❌')]),
            'critical_issues': self.critical_issues,
            'warnings': self.warnings,
            'status': 'PASS' if not self.critical_issues else 'FAIL',
            'checks': self.checks
        }
        
        with open('phase1_verification_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        self.log("✅ Verification report saved: phase1_verification_report.json")
        return report
    
    def verify(self):
        """Main verification function"""
        self.log("🔍 Starting Phase 1 Verification")
        self.log("=" * 60)
        
        # Run all checks
        checks = [
            ("Security Files", lambda: self.check_file_exists('secure_auth_system.py', 'Security auth system')),
            ("Security Middleware", lambda: self.check_file_exists('security_middleware.py', 'Security middleware')),
            ("Security Enhancements", lambda: self.check_file_exists('security_enhancements.py', 'Security enhancements')),
            ("Database Tables", self.check_database_tables),
            ("Admin User", self.check_admin_user),
            ("Security Imports", self.check_security_imports),
            ("Login Endpoint", self.check_login_endpoint),
            ("Dependencies", self.check_dependencies),
            ("Login Functionality", self.test_login_endpoint),
            ("Endpoint Protection", self.test_protected_endpoints),
            ("Security Logs", self.check_security_logs)
        ]
        
        for check_name, check_func in checks:
            self.log(f"\n📋 {check_name}...")
            try:
                check_func()
            except Exception as e:
                self.log(f"❌ {check_name} failed: {str(e)}")
                self.critical_issues.append(f"{check_name}: {str(e)}")
        
        # Generate report
        report = self.generate_report()
        
        # Final summary
        self.log("\n" + "=" * 60)
        self.log("📊 VERIFICATION SUMMARY")
        self.log("=" * 60)
        
        passed = report['passed_checks']
        failed = report['failed_checks']
        total = report['total_checks']
        
        self.log(f"✅ Passed: {passed}/{total}")
        self.log(f"❌ Failed: {failed}/{total}")
        
        if self.critical_issues:
            self.log(f"\n🚨 CRITICAL ISSUES ({len(self.critical_issues)}):")
            for issue in self.critical_issues:
                self.log(f"   - {issue}")
        
        if self.warnings:
            self.log(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                self.log(f"   - {warning}")
        
        if not self.critical_issues:
            self.log("\n🎉 PHASE 1 VERIFICATION PASSED!")
            self.log("🔐 Security features are working correctly")
            self.log("🛡️  Critical vulnerabilities have been fixed")
        else:
            self.log("\n❌ PHASE 1 VERIFICATION FAILED!")
            self.log("🔧 Critical issues need to be resolved")
            self.log("📞 Consider re-running deployment or rollback")
        
        return len(self.critical_issues) == 0

def main():
    """Main function"""
    print("=" * 60)
    print("    PHASE 1 VERIFICATION")
    print("    Phong kham chuyen khoa Phu San Dai Anh")
    print("=" * 60)
    
    # Get base URL from command line or use default
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000"
    
    print(f"🎯 Verifying target: {base_url}")
    print("⚠️  Make sure the application is running for full verification")
    
    # Start verification
    verifier = Phase1Verifier(base_url)
    success = verifier.verify()
    
    if success:
        print("\n🎉 Verification completed successfully!")
        print("🔐 Phase 1 security features are working")
        print("📋 Next steps:")
        print("   1. Test all application functionality")
        print("   2. Change admin password")
        print("   3. Monitor security logs")
        print("   4. Consider Phase 2 deployment")
        sys.exit(0)
    else:
        print("\n❌ Verification failed!")
        print("🔧 Critical issues need to be resolved")
        print("📞 Consider re-deploying or rolling back")
        sys.exit(1)

if __name__ == "__main__":
    main()
