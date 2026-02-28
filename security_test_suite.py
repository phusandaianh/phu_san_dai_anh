#!/usr/bin/env python3
"""
Security test suite cho hệ thống Phòng khám Đại Anh
Kiểm tra các lỗ hổng bảo mật và đề xuất cải tiến
"""

import requests
import json
import time
import threading
from datetime import datetime
import re
import os
import sys

class SecurityTester:
    """Security testing suite"""
    
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.vulnerabilities = []
        self.recommendations = []
    
    def test_authentication_bypass(self):
        """Test authentication bypass"""
        print("🔍 Testing authentication bypass...")
        
        # Test endpoints that should require authentication
        protected_endpoints = [
            '/api/admin/appointments',
            '/api/patients',
            '/api/voluson/config',
            '/api/lab-orders'
        ]
        
        for endpoint in protected_endpoints:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}")
                if response.status_code == 200:
                    self.vulnerabilities.append({
                        'type': 'AUTHENTICATION_BYPASS',
                        'severity': 'CRITICAL',
                        'endpoint': endpoint,
                        'description': f'Endpoint {endpoint} accessible without authentication'
                    })
            except Exception as e:
                print(f"Error testing {endpoint}: {e}")
    
    def test_sql_injection(self):
        """Test SQL injection vulnerabilities"""
        print("🔍 Testing SQL injection...")
        
        # Test parameters for SQL injection
        sql_payloads = [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "' UNION SELECT * FROM users --",
            "1' OR '1'='1' --",
            "admin'--",
            "admin'/*"
        ]
        
        # Test endpoints with parameters
        test_endpoints = [
            '/api/patients?q=',
            '/api/appointments?patient_id=',
            '/api/lab-orders?q='
        ]
        
        for endpoint in test_endpoints:
            for payload in sql_payloads:
                try:
                    response = self.session.get(f"{self.base_url}{endpoint}{payload}")
                    if 'error' in response.text.lower() or 'sql' in response.text.lower():
                        self.vulnerabilities.append({
                            'type': 'SQL_INJECTION',
                            'severity': 'CRITICAL',
                            'endpoint': endpoint,
                            'payload': payload,
                            'description': f'Potential SQL injection in {endpoint}'
                        })
                except Exception as e:
                    print(f"Error testing SQL injection: {e}")
    
    def test_xss_vulnerabilities(self):
        """Test XSS vulnerabilities"""
        print("🔍 Testing XSS vulnerabilities...")
        
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<svg onload=alert('XSS')>",
            "';alert('XSS');//"
        ]
        
        # Test POST endpoints
        test_data = {
            'name': '',
            'phone': '',
            'address': '',
            'service_type': ''
        }
        
        for payload in xss_payloads:
            for field in test_data:
                test_data[field] = payload
                try:
                    response = self.session.post(f"{self.base_url}/api/appointments", 
                                               json=test_data)
                    if payload in response.text:
                        self.vulnerabilities.append({
                            'type': 'XSS',
                            'severity': 'HIGH',
                            'field': field,
                            'payload': payload,
                            'description': f'XSS vulnerability in {field} field'
                        })
                except Exception as e:
                    print(f"Error testing XSS: {e}")
    
    def test_rate_limiting(self):
        """Test rate limiting"""
        print("🔍 Testing rate limiting...")
        
        # Test rate limiting on login endpoint
        login_data = {
            'username': 'test',
            'password': 'test'
        }
        
        start_time = time.time()
        requests_count = 0
        
        for i in range(100):  # Send 100 requests quickly
            try:
                response = self.session.post(f"{self.base_url}/api/login", 
                                           json=login_data)
                requests_count += 1
                
                if response.status_code == 429:  # Rate limited
                    break
            except Exception as e:
                print(f"Error testing rate limiting: {e}")
        
        elapsed_time = time.time() - start_time
        
        if requests_count > 50:  # If more than 50 requests succeeded
            self.vulnerabilities.append({
                'type': 'RATE_LIMITING',
                'severity': 'MEDIUM',
                'description': f'No rate limiting detected. {requests_count} requests in {elapsed_time:.2f}s'
            })
    
    def test_file_upload_security(self):
        """Test file upload security"""
        print("🔍 Testing file upload security...")
        
        # Test malicious file uploads
        malicious_files = [
            ('test.php', '<?php system($_GET["cmd"]); ?>'),
            ('test.jsp', '<% Runtime.getRuntime().exec(request.getParameter("cmd")); %>'),
            ('test.html', '<script>alert("XSS")</script>'),
            ('test.exe', b'\x4d\x5a\x90\x00')  # PE header
        ]
        
        for filename, content in malicious_files:
            try:
                files = {'file': (filename, content)}
                response = self.session.post(f"{self.base_url}/api/upload", files=files)
                
                if response.status_code == 200:
                    self.vulnerabilities.append({
                        'type': 'FILE_UPLOAD',
                        'severity': 'HIGH',
                        'filename': filename,
                        'description': f'Malicious file {filename} uploaded successfully'
                    })
            except Exception as e:
                print(f"Error testing file upload: {e}")
    
    def test_information_disclosure(self):
        """Test information disclosure"""
        print("🔍 Testing information disclosure...")
        
        # Test common information disclosure endpoints
        disclosure_endpoints = [
            '/.env',
            '/config.json',
            '/backup.sql',
            '/database.db',
            '/admin',
            '/phpmyadmin',
            '/.git',
            '/robots.txt',
            '/sitemap.xml'
        ]
        
        for endpoint in disclosure_endpoints:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}")
                if response.status_code == 200:
                    # Check if response contains sensitive information
                    sensitive_keywords = ['password', 'secret', 'key', 'token', 'database']
                    content = response.text.lower()
                    
                    for keyword in sensitive_keywords:
                        if keyword in content:
                            self.vulnerabilities.append({
                                'type': 'INFORMATION_DISCLOSURE',
                                'severity': 'MEDIUM',
                                'endpoint': endpoint,
                                'keyword': keyword,
                                'description': f'Sensitive information disclosed in {endpoint}'
                            })
                            break
            except Exception as e:
                print(f"Error testing information disclosure: {e}")
    
    def test_csrf_protection(self):
        """Test CSRF protection"""
        print("🔍 Testing CSRF protection...")
        
        # Test CSRF on state-changing endpoints
        csrf_endpoints = [
            '/api/appointments',
            '/api/patients',
            '/api/admin/settings'
        ]
        
        for endpoint in csrf_endpoints:
            try:
                # Test without CSRF token
                response = self.session.post(f"{self.base_url}{endpoint}", 
                                           json={'test': 'data'})
                
                if response.status_code == 200:
                    self.vulnerabilities.append({
                        'type': 'CSRF',
                        'severity': 'MEDIUM',
                        'endpoint': endpoint,
                        'description': f'CSRF protection missing on {endpoint}'
                    })
            except Exception as e:
                print(f"Error testing CSRF: {e}")
    
    def test_https_enforcement(self):
        """Test HTTPS enforcement"""
        print("🔍 Testing HTTPS enforcement...")
        
        try:
            # Test if HTTP redirects to HTTPS
            response = self.session.get(f"http://localhost:5000", allow_redirects=False)
            
            if response.status_code != 301 and response.status_code != 302:
                self.vulnerabilities.append({
                    'type': 'HTTPS_ENFORCEMENT',
                    'severity': 'MEDIUM',
                    'description': 'HTTPS not enforced - HTTP requests accepted'
                })
        except Exception as e:
            print(f"Error testing HTTPS enforcement: {e}")
    
    def test_security_headers(self):
        """Test security headers"""
        print("🔍 Testing security headers...")
        
        try:
            response = self.session.get(f"{self.base_url}/")
            headers = response.headers
            
            required_headers = {
                'X-Content-Type-Options': 'nosniff',
                'X-Frame-Options': 'DENY',
                'X-XSS-Protection': '1; mode=block',
                'Strict-Transport-Security': 'max-age=31536000',
                'Content-Security-Policy': 'default-src \'self\''
            }
            
            for header, expected_value in required_headers.items():
                if header not in headers:
                    self.vulnerabilities.append({
                        'type': 'SECURITY_HEADERS',
                        'severity': 'LOW',
                        'header': header,
                        'description': f'Missing security header: {header}'
                    })
                elif expected_value not in headers[header]:
                    self.vulnerabilities.append({
                        'type': 'SECURITY_HEADERS',
                        'severity': 'LOW',
                        'header': header,
                        'description': f'Incorrect security header value: {header}'
                    })
        except Exception as e:
            print(f"Error testing security headers: {e}")
    
    def test_session_security(self):
        """Test session security"""
        print("🔍 Testing session security...")
        
        try:
            # Test session fixation
            response1 = self.session.get(f"{self.base_url}/")
            session_id_1 = self.session.cookies.get('session')
            
            # Login attempt
            login_data = {'username': 'admin', 'password': 'admin'}
            response2 = self.session.post(f"{self.base_url}/api/login", json=login_data)
            session_id_2 = self.session.cookies.get('session')
            
            if session_id_1 == session_id_2:
                self.vulnerabilities.append({
                    'type': 'SESSION_FIXATION',
                    'severity': 'MEDIUM',
                    'description': 'Session ID not changed after login'
                })
        except Exception as e:
            print(f"Error testing session security: {e}")
    
    def generate_report(self):
        """Generate security report"""
        print("\n" + "="*60)
        print("    SECURITY TEST REPORT")
        print("    Phòng khám chuyên khoa Phụ Sản Đại Anh")
        print("="*60)
        
        # Count vulnerabilities by severity
        critical_count = len([v for v in self.vulnerabilities if v['severity'] == 'CRITICAL'])
        high_count = len([v for v in self.vulnerabilities if v['severity'] == 'HIGH'])
        medium_count = len([v for v in self.vulnerabilities if v['severity'] == 'MEDIUM'])
        low_count = len([v for v in self.vulnerabilities if v['severity'] == 'LOW'])
        
        print(f"\n📊 TỔNG KẾT:")
        print(f"   🔴 Critical: {critical_count}")
        print(f"   🟠 High: {high_count}")
        print(f"   🟡 Medium: {medium_count}")
        print(f"   🟢 Low: {low_count}")
        print(f"   📈 Total: {len(self.vulnerabilities)}")
        
        if critical_count > 0:
            print(f"\n🚨 CẢNH BÁO: {critical_count} lỗ hổng NGHIÊM TRỌNG cần khắc phục ngay!")
        
        # Detailed vulnerabilities
        print(f"\n🔍 CHI TIẾT CÁC LỖ HỔNG:")
        for i, vuln in enumerate(self.vulnerabilities, 1):
            severity_icon = {
                'CRITICAL': '🔴',
                'HIGH': '🟠',
                'MEDIUM': '🟡',
                'LOW': '🟢'
            }.get(vuln['severity'], '⚪')
            
            print(f"\n{i}. {severity_icon} {vuln['type']} ({vuln['severity']})")
            print(f"   📍 {vuln.get('endpoint', vuln.get('field', 'N/A'))}")
            print(f"   📝 {vuln['description']}")
            
            if 'payload' in vuln:
                print(f"   💉 Payload: {vuln['payload']}")
        
        # Recommendations
        print(f"\n💡 KHUYẾN NGHỊ:")
        print("1. 🔐 Triển khai authentication system ngay lập tức")
        print("2. 🛡️ Thêm input validation và sanitization")
        print("3. 🔒 Mã hóa dữ liệu nhạy cảm")
        print("4. 📊 Thêm audit logging")
        print("5. 🚦 Cấu hình rate limiting")
        print("6. 🔐 Bật HTTPS enforcement")
        print("7. 📋 Thêm security headers")
        print("8. 🔍 Triển khai security monitoring")
        
        # Save report to file
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'total_vulnerabilities': len(self.vulnerabilities),
            'critical': critical_count,
            'high': high_count,
            'medium': medium_count,
            'low': low_count,
            'vulnerabilities': self.vulnerabilities
        }
        
        with open('security_test_report.json', 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Báo cáo chi tiết đã được lưu vào: security_test_report.json")
        
        return report_data
    
    def run_all_tests(self):
        """Chạy tất cả các test bảo mật"""
        print("🚀 Bắt đầu kiểm tra bảo mật...")
        
        # Chạy tất cả tests
        self.test_authentication_bypass()
        self.test_sql_injection()
        self.test_xss_vulnerabilities()
        self.test_rate_limiting()
        self.test_file_upload_security()
        self.test_information_disclosure()
        self.test_csrf_protection()
        self.test_https_enforcement()
        self.test_security_headers()
        self.test_session_security()
        
        # Generate report
        return self.generate_report()

def main():
    """Main function"""
    print("="*60)
    print("    SECURITY TEST SUITE")
    print("    Phòng khám chuyên khoa Phụ Sản Đại Anh")
    print("="*60)
    
    # Get base URL from command line or use default
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000"
    
    print(f"🎯 Testing target: {base_url}")
    print("⚠️  Lưu ý: Đảm bảo ứng dụng đang chạy trước khi test")
    
    # Create tester instance
    tester = SecurityTester(base_url)
    
    # Run all tests
    try:
        report = tester.run_all_tests()
        
        # Exit with appropriate code
        if report['critical'] > 0:
            print("\n🚨 KẾT QUẢ: CÓ LỖ HỔNG NGHIÊM TRỌNG!")
            sys.exit(1)
        elif report['high'] > 0:
            print("\n⚠️  KẾT QUẢ: CÓ LỖ HỔNG MỨC ĐỘ CAO!")
            sys.exit(2)
        else:
            print("\n✅ KẾT QUẢ: KHÔNG CÓ LỖ HỔNG NGHIÊM TRỌNG!")
            sys.exit(0)
            
    except Exception as e:
        print(f"\n❌ Lỗi khi chạy test: {e}")
        sys.exit(3)

if __name__ == "__main__":
    main()
