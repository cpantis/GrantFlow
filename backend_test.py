#!/usr/bin/env python3
import requests
import sys
import json
import uuid
from datetime import datetime

class GrantFlowAPITester:
    def __init__(self):
        self.base_url = "https://implementation-guide-1.preview.emergentagent.com/api"
        self.token = None
        self.user_data = None
        self.tests_run = 0
        self.tests_passed = 0
        self.org_id = None
        self.project_id = None
        self.doc_id = None
        
        # Test user data
        self.test_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        self.test_password = "TestPass123!"
        self.test_user = {
            "email": self.test_email,
            "password": self.test_password,
            "nume": "TestNume",
            "prenume": "TestPrenume",
            "telefon": "0722123456"
        }
        
        # RBAC test data
        self.second_user_email = f"imputernicit_{uuid.uuid4().hex[:8]}@example.com"
        self.second_user_password = "TestPass123!"
        self.second_user = {
            "email": self.second_user_email,
            "password": self.second_user_password,
            "nume": "ImputernicitNume",
            "prenume": "ImputernicitPrenume",
            "telefon": "0722654321"
        }
        self.second_token = None
        self.second_user_data = None
        
        # Email verification and password reset tokens
        self.verification_token = None
        self.reset_token = None

    def log_test(self, name, method, endpoint, expected_status, result, response_data=None, error=None):
        """Log test result"""
        status = "✅ PASSED" if result else "❌ FAILED"
        self.tests_run += 1
        if result:
            self.tests_passed += 1
        
        print(f"\n{status} | {method} {endpoint}")
        print(f"   Test: {name}")
        print(f"   Expected: {expected_status}")
        if error:
            print(f"   Error: {error}")
        if response_data and isinstance(response_data, dict):
            print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
        return result

    def api_request(self, method, endpoint, data=None, files=None, expected_status=200):
        """Make API request with error handling"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        if files:
            headers.pop('Content-Type', None)  # Let requests set it for multipart
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                if files:
                    response = requests.post(url, headers={k: v for k, v in headers.items() if k != 'Content-Type'}, 
                                           files=files, data=data, timeout=30)
                else:
                    response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)
            
            success = response.status_code == expected_status
            response_data = None
            
            try:
                if response.content:
                    response_data = response.json()
            except:
                response_data = {"raw_response": response.text[:500]}
            
            if not success:
                error = f"Status {response.status_code}, Expected {expected_status}. Response: {response.text[:200]}"
                return False, response_data, error
                
            return True, response_data, None
            
        except Exception as e:
            return False, None, str(e)

    # ============ AUTH TESTS ============
    
    def test_auth_register(self):
        """Test user registration"""
        success, data, error = self.api_request('POST', 'auth/register', self.test_user, expected_status=200)
        result = self.log_test("User Registration", "POST", "/auth/register", 200, success, data, error)
        
        if success and data:
            self.token = data.get('token')
            self.user_data = data.get('user')
            self.verification_token = data.get('verification_token')  # For email verification testing
            
        return result

    def test_auth_login(self):
        """Test user login"""
        login_data = {"email": self.test_email, "password": self.test_password}
        success, data, error = self.api_request('POST', 'auth/login', login_data, expected_status=200)
        result = self.log_test("User Login", "POST", "/auth/login", 200, success, data, error)
        
        if success and data:
            self.token = data.get('token')
            self.user_data = data.get('user')
            
        return result

    def test_auth_me(self):
        """Test get user profile"""
        success, data, error = self.api_request('GET', 'auth/me', expected_status=200)
        return self.log_test("Get User Profile", "GET", "/auth/me", 200, success, data, error)

    # ============ ORGANIZATION TESTS ============
    
    def test_org_create(self):
        """Test organization creation with mock CUI"""
        org_data = {"cui": "12345678"}  # Using test CUI from requirements
        success, data, error = self.api_request('POST', 'organizations', org_data, expected_status=200)
        result = self.log_test("Create Organization", "POST", "/organizations", 200, success, data, error)
        
        if success and data:
            self.org_id = data.get('id')
            
        return result

    def test_org_list(self):
        """Test list organizations"""
        success, data, error = self.api_request('GET', 'organizations', expected_status=200)
        return self.log_test("List Organizations", "GET", "/organizations", 200, success, data, error)

    def test_org_detail(self):
        """Test get organization detail"""
        if not self.org_id:
            return self.log_test("Get Organization Detail", "GET", f"/organizations/{self.org_id}", 200, False, None, "No org_id available")
        
        success, data, error = self.api_request('GET', f'organizations/{self.org_id}', expected_status=200)
        return self.log_test("Get Organization Detail", "GET", f"/organizations/{self.org_id}", 200, success, data, error)

    def test_org_financial(self):
        """Test get organization financial data"""
        if not self.org_id:
            return self.log_test("Get Organization Financial", "GET", f"/organizations/{self.org_id}/financial", 200, False, None, "No org_id available")
        
        success, data, error = self.api_request('GET', f'organizations/{self.org_id}/financial', expected_status=200)
        return self.log_test("Get Organization Financial", "GET", f"/organizations/{self.org_id}/financial", 200, success, data, error)

    # ============ PROJECT TESTS ============
    
    def test_project_create(self):
        """Test project creation"""
        if not self.org_id:
            return self.log_test("Create Project", "POST", "/projects", 200, False, None, "No org_id available")
            
        project_data = {
            "titlu": "Test Project GrantFlow",
            "organizatie_id": self.org_id,
            "program_finantare": "POC 2021-2027",
            "descriere": "Test project for API validation",
            "buget_estimat": 100000,
            "obiective": ["Obiectiv 1", "Obiectiv 2"]
        }
        success, data, error = self.api_request('POST', 'projects', project_data, expected_status=200)
        result = self.log_test("Create Project", "POST", "/projects", 200, success, data, error)
        
        if success and data:
            self.project_id = data.get('id')
            
        return result

    def test_project_list(self):
        """Test list projects"""
        success, data, error = self.api_request('GET', 'projects', expected_status=200)
        return self.log_test("List Projects", "GET", "/projects", 200, success, data, error)

    def test_project_states(self):
        """Test get project states"""
        success, data, error = self.api_request('GET', 'projects/states', expected_status=200)
        return self.log_test("Get Project States", "GET", "/projects/states", 200, success, data, error)

    def test_project_transition(self):
        """Test project state transition"""
        if not self.project_id:
            return self.log_test("Project State Transition", "POST", f"/projects/{self.project_id}/transition", 200, False, None, "No project_id available")
            
        transition_data = {
            "new_state": "pre_eligibil",
            "motiv": "Test transition from draft to pre_eligibil"
        }
        success, data, error = self.api_request('POST', f'projects/{self.project_id}/transition', transition_data, expected_status=200)
        return self.log_test("Project State Transition", "POST", f"/projects/{self.project_id}/transition", 200, success, data, error)

    # ============ DOCUMENT TESTS ============
    
    def test_document_upload(self):
        """Test document upload"""
        if not self.org_id:
            return self.log_test("Document Upload", "POST", "/documents/upload", 200, False, None, "No org_id available")
            
        # Create a simple test file
        test_content = b"Test document content for GrantFlow API testing"
        files = {'file': ('test_document.txt', test_content, 'text/plain')}
        data = {
            'organizatie_id': self.org_id,
            'project_id': self.project_id or '',
            'tip': 'cerere_finantare',
            'descriere': 'Test document upload'
        }
        
        success, response_data, error = self.api_request('POST', 'documents/upload', data=data, files=files, expected_status=200)
        result = self.log_test("Document Upload", "POST", "/documents/upload", 200, success, response_data, error)
        
        if success and response_data:
            self.doc_id = response_data.get('id')
            
        return result

    def test_document_list(self):
        """Test list documents"""
        success, data, error = self.api_request('GET', 'documents', expected_status=200)
        return self.log_test("List Documents", "GET", "/documents", 200, success, data, error)

    # ============ COMPLIANCE TESTS ============
    
    def test_compliance_submission_ready(self):
        """Test submission readiness check"""
        if not self.project_id:
            return self.log_test("Check Submission Ready", "POST", f"/compliance/submission-ready/{self.project_id}", 200, False, None, "No project_id available")
            
        success, data, error = self.api_request('POST', f'compliance/submission-ready/{self.project_id}', expected_status=200)
        return self.log_test("Check Submission Ready", "POST", f"/compliance/submission-ready/{self.project_id}", 200, success, data, error)

    # ============ ADMIN TESTS ============
    
    def test_admin_dashboard(self):
        """Test admin dashboard"""
        success, data, error = self.api_request('GET', 'admin/dashboard', expected_status=200)
        return self.log_test("Admin Dashboard", "GET", "/admin/dashboard", 200, success, data, error)

    def test_admin_audit_log(self):
        """Test audit log"""
        success, data, error = self.api_request('GET', 'admin/audit-log', expected_status=200)
        return self.log_test("Admin Audit Log", "GET", "/admin/audit-log", 200, success, data, error)

    def run_all_tests(self):
        """Run all backend API tests"""
        print("="*60)
        print("🚀 STARTING GRANTFLOW BACKEND API TESTING")
        print("="*60)
        print(f"Base URL: {self.base_url}")
        print(f"Test Email: {self.test_email}")
        print(f"Test Date: {datetime.now().isoformat()}")
        
        # Authentication flow
        print("\n" + "="*40)
        print("🔐 AUTHENTICATION TESTS")
        print("="*40)
        
        if not self.test_auth_register():
            print("❌ Registration failed - stopping tests")
            return self.print_summary()
            
        if not self.test_auth_login():
            print("❌ Login failed - trying to continue with registration token")
            
        self.test_auth_me()
        
        # Organization tests
        print("\n" + "="*40)
        print("🏢 ORGANIZATION TESTS")
        print("="*40)
        
        self.test_org_create()
        self.test_org_list()
        self.test_org_detail()
        self.test_org_financial()
        
        # Project tests
        print("\n" + "="*40)
        print("📋 PROJECT TESTS")
        print("="*40)
        
        self.test_project_create()
        self.test_project_list()
        self.test_project_states()
        self.test_project_transition()
        
        # Document tests
        print("\n" + "="*40)
        print("📄 DOCUMENT TESTS")
        print("="*40)
        
        self.test_document_upload()
        self.test_document_list()
        
        # Compliance tests
        print("\n" + "="*40)
        print("✅ COMPLIANCE TESTS")
        print("="*40)
        
        self.test_compliance_submission_ready()
        
        # Admin tests
        print("\n" + "="*40)
        print("👑 ADMIN TESTS")
        print("="*40)
        
        self.test_admin_dashboard()
        self.test_admin_audit_log()
        
        return self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "No tests run")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL TESTS PASSED!")
            return 0
        else:
            print("⚠️  SOME TESTS FAILED")
            return 1

if __name__ == "__main__":
    tester = GrantFlowAPITester()
    exit_code = tester.run_all_tests()
    sys.exit(exit_code)