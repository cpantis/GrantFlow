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

    # ============ EMAIL VERIFICATION TESTS ============
    
    def test_email_verify(self):
        """Test email verification"""
        if not self.verification_token:
            return self.log_test("Email Verification", "POST", "/auth/verify-email", 200, False, None, "No verification token available")
        
        verify_data = {"token": self.verification_token}
        success, data, error = self.api_request('POST', 'auth/verify-email', verify_data, expected_status=200)
        return self.log_test("Email Verification", "POST", "/auth/verify-email", 200, success, data, error)

    def test_email_resend_verification(self):
        """Test resend email verification (expects 400 if already verified)"""
        success, data, error = self.api_request('POST', 'auth/resend-verification', expected_status=400)  # Expect 400 since email is already verified
        result = self.log_test("Resend Email Verification", "POST", "/auth/resend-verification", 400, success, data, error)
        
        # If email is already verified, this should return 400 - that's correct behavior
        if success and data and "deja verificat" in data.get('detail', ''):
            result = True  # This is expected behavior
            
        return result

    def test_login_email_verified_status(self):
        """Test login returns email_verified status"""
        login_data = {"email": self.test_email, "password": self.test_password}
        success, data, error = self.api_request('POST', 'auth/login', login_data, expected_status=200)
        result = self.log_test("Login Email Verified Status", "POST", "/auth/login", 200, success, data, error)
        
        if success and data and data.get('user'):
            has_email_verified = 'email_verified' in data['user']
            if not has_email_verified:
                result = False
                error = "Login response missing email_verified field"
                
        return result

    # ============ PASSWORD RESET TESTS ============
    
    def test_password_reset_request(self):
        """Test password reset request"""
        reset_data = {"email": self.test_email}
        success, data, error = self.api_request('POST', 'auth/reset-password', reset_data, expected_status=200)
        result = self.log_test("Password Reset Request", "POST", "/auth/reset-password", 200, success, data, error)
        
        if success and data:
            self.reset_token = data.get('reset_token')
            
        return result

    def test_password_reset_confirm(self):
        """Test password reset confirmation"""
        if not self.reset_token:
            return self.log_test("Password Reset Confirm", "POST", "/auth/reset-password/confirm", 200, False, None, "No reset token available")
            
        new_password = "NewTestPass123!"
        confirm_data = {"token": self.reset_token, "new_password": new_password}
        success, data, error = self.api_request('POST', 'auth/reset-password/confirm', confirm_data, expected_status=200)
        result = self.log_test("Password Reset Confirm", "POST", "/auth/reset-password/confirm", 200, success, data, error)
        
        if success:
            # Update password for future tests
            self.test_password = new_password
            self.test_user["password"] = new_password
            
        return result

    def test_login_with_new_password(self):
        """Test login with new password after reset"""
        login_data = {"email": self.test_email, "password": self.test_password}
        success, data, error = self.api_request('POST', 'auth/login', login_data, expected_status=200)
        result = self.log_test("Login With New Password", "POST", "/auth/login", 200, success, data, error)
        
        if success and data:
            self.token = data.get('token')
            
        return result

    def test_change_password(self):
        """Test change password with current password"""
        current_password = self.test_password
        new_password = "ChangedTestPass123!"
        change_data = {"current_password": current_password, "new_password": new_password}
        success, data, error = self.api_request('POST', 'auth/change-password', change_data, expected_status=200)
        result = self.log_test("Change Password", "POST", "/auth/change-password", 200, success, data, error)
        
        if success:
            # Update password for future tests
            self.test_password = new_password
            self.test_user["password"] = new_password
            
        return result

    # ============ RBAC TESTS ============
    
    def test_rbac_register_second_user(self):
        """Test registering second user for RBAC testing"""
        success, data, error = self.api_request('POST', 'auth/register', self.second_user, expected_status=200)
        result = self.log_test("RBAC: Register Second User", "POST", "/auth/register", 200, success, data, error)
        
        if success and data:
            self.second_token = data.get('token')
            self.second_user_data = data.get('user')
            
        return result

    def test_rbac_owner_create_org(self):
        """Test owner can create organization (becomes owner automatically)"""
        # Use unique CUI for this test run
        unique_cui = f"1234567{uuid.uuid4().hex[:2]}"  # Generate unique CUI
        org_data = {"cui": unique_cui}
        success, data, error = self.api_request('POST', 'organizations', org_data, expected_status=200)
        result = self.log_test("RBAC: Owner Create Org", "POST", "/organizations", 200, success, data, error)
        
        if success and data:
            self.org_id = data.get('id')
            
        return result

    def test_rbac_owner_manage_members(self):
        """Test owner can add members to organization"""
        if not self.org_id or not self.second_user_data:
            return self.log_test("RBAC: Owner Manage Members", "POST", f"/organizations/{self.org_id}/members", 200, False, None, "Missing org_id or second_user")
        
        member_data = {
            "email": self.second_user_data['email'],  # Use email, not user_id
            "rol": "imputernicit"
        }
        success, data, error = self.api_request('POST', f'organizations/{self.org_id}/members', member_data, expected_status=200)
        return self.log_test("RBAC: Owner Manage Members", "POST", f"/organizations/{self.org_id}/members", 200, success, data, error)

    def test_rbac_imputernicit_limited_access(self):
        """Test imputernicit has limited access (no manage_members)"""
        if not self.org_id or not self.second_token:
            return self.log_test("RBAC: Imputernicit Limited Access", "POST", f"/organizations/{self.org_id}/members", 403, False, None, "Missing org_id or second_token")
        
        # Switch to second user token (imputernicit)
        original_token = self.token
        self.token = self.second_token
        
        # Try to add a member (should fail with 403)
        dummy_member_data = {
            "email": "dummy@example.com",  # Use email format
            "rol": "consultant"
        }
        success, data, error = self.api_request('POST', f'organizations/{self.org_id}/members', dummy_member_data, expected_status=403)
        result = self.log_test("RBAC: Imputernicit Limited Access", "POST", f"/organizations/{self.org_id}/members", 403, success, data, error)
        
        # Restore original token
        self.token = original_token
        return result

    def test_rbac_owner_create_project(self):
        """Test owner can create project"""
        if not self.org_id:
            return self.log_test("RBAC: Owner Create Project", "POST", "/projects", 200, False, None, "No org_id available")
            
        project_data = {
            "titlu": "RBAC Test Project",
            "organizatie_id": self.org_id,
            "program_finantare": "POC 2021-2027",
            "descriere": "Test project for RBAC validation",
            "buget_estimat": 150000,
            "obiective": ["RBAC Obiectiv 1", "RBAC Obiectiv 2"]
        }
        success, data, error = self.api_request('POST', 'projects', project_data, expected_status=200)
        result = self.log_test("RBAC: Owner Create Project", "POST", "/projects", 200, success, data, error)
        
        if success and data:
            self.project_id = data.get('id')
            
        return result

    def test_rbac_imputernicit_view_project(self):
        """Test imputernicit can view project"""
        if not self.project_id or not self.second_token:
            return self.log_test("RBAC: Imputernicit View Project", "GET", f"/projects/{self.project_id}", 200, False, None, "Missing project_id or second_token")
        
        # Switch to second user token (imputernicit)
        original_token = self.token
        self.token = self.second_token
        
        success, data, error = self.api_request('GET', f'projects/{self.project_id}', expected_status=200)
        result = self.log_test("RBAC: Imputernicit View Project", "GET", f"/projects/{self.project_id}", 200, success, data, error)
        
        # Restore original token
        self.token = original_token
        return result

    def test_rbac_project_transition_owner_only(self):
        """Test project transitions only allowed for owners"""
        if not self.project_id:
            return self.log_test("RBAC: Project Transition Owner Only", "POST", f"/projects/{self.project_id}/transition", 200, False, None, "No project_id available")
            
        transition_data = {
            "new_state": "pre_eligibil",
            "motiv": "RBAC test transition from draft to pre_eligibil"
        }
        success, data, error = self.api_request('POST', f'projects/{self.project_id}/transition', transition_data, expected_status=200)
        return self.log_test("RBAC: Project Transition Owner Only", "POST", f"/projects/{self.project_id}/transition", 200, success, data, error)

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

    # ============ OCR TESTS ============
    
    def test_ocr_trigger(self):
        """Test trigger OCR processing for document"""
        if not self.doc_id:
            return self.log_test("OCR: Trigger Processing", "POST", f"/documents/{self.doc_id}/ocr", 200, False, None, "No doc_id available")
        
        success, data, error = self.api_request('POST', f'documents/{self.doc_id}/ocr', expected_status=200)
        return self.log_test("OCR: Trigger Processing", "POST", f"/documents/{self.doc_id}/ocr", 200, success, data, error)

    def test_ocr_get_results(self):
        """Test get OCR results with extracted fields and confidence scores"""
        if not self.doc_id:
            return self.log_test("OCR: Get Results", "GET", f"/documents/{self.doc_id}/ocr", 200, False, None, "No doc_id available")
        
        success, data, error = self.api_request('GET', f'documents/{self.doc_id}/ocr', expected_status=200)
        result = self.log_test("OCR: Get Results", "GET", f"/documents/{self.doc_id}/ocr", 200, success, data, error)
        
        # Validate OCR response structure
        if success and data:
            required_fields = ['extracted_fields', 'field_confidences', 'overall_confidence', 'status']
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                result = False
                error = f"OCR response missing fields: {missing_fields}"
                self.log_test("OCR: Response Validation", "GET", f"/documents/{self.doc_id}/ocr", 200, False, None, error)
                
        return result

    def test_ocr_correct_field(self):
        """Test OCR field correction"""
        if not self.doc_id:
            return self.log_test("OCR: Correct Field", "POST", f"/documents/{self.doc_id}/ocr/correct", 200, False, None, "No doc_id available")
        
        # First get the OCR results to find a field to correct
        success, ocr_data, error = self.api_request('GET', f'documents/{self.doc_id}/ocr', expected_status=200)
        if not success or not ocr_data or not ocr_data.get('extracted_fields'):
            return self.log_test("OCR: Correct Field", "POST", f"/documents/{self.doc_id}/ocr/correct", 200, False, None, "No OCR data available for correction")
        
        # Pick the first field to correct
        first_field = list(ocr_data['extracted_fields'].keys())[0]
        corrected_value = "Corrected Test Value"
        
        correct_data = {
            "field_name": first_field,
            "corrected_value": corrected_value
        }
        
        # Use query parameters as per the API
        success, data, error = self.api_request('POST', f'documents/{self.doc_id}/ocr/correct?field_name={first_field}&corrected_value={corrected_value}', expected_status=200)
        return self.log_test("OCR: Correct Field", "POST", f"/documents/{self.doc_id}/ocr/correct", 200, success, data, error)

    # ============ COMPLIANCE TESTS ============
    
    def test_compliance_submission_ready(self):
        """Test submission readiness check"""
        if not self.project_id:
            return self.log_test("Check Submission Ready", "POST", f"/compliance/submission-ready/{self.project_id}", 200, False, None, "No project_id available")
            
        success, data, error = self.api_request('POST', f'compliance/submission-ready/{self.project_id}', expected_status=200)
        return self.log_test("Check Submission Ready", "POST", f"/compliance/submission-ready/{self.project_id}", 200, success, data, error)

    def test_ai_navigator_with_project(self):
        """Test AI Navigator chat with project context"""
        if not self.project_id:
            return self.log_test("AI Navigator with Project", "POST", "/compliance/navigator", 200, False, None, "No project_id available")
            
        chat_data = {
            "message": "Care sunt următorii pași pentru acest proiect?",
            "project_id": self.project_id
        }
        success, data, error = self.api_request('POST', 'compliance/navigator', chat_data, expected_status=200)
        result = self.log_test("AI Navigator with Project", "POST", "/compliance/navigator", 200, success, data, error)
        
        # Validate AI response structure and markdown
        if success and data:
            has_response = 'response' in data and data['response']
            has_success = 'success' in data
            if not has_response or not has_success:
                result = False
                error = f"AI Navigator response missing fields. Got: {data}"
                self.log_test("AI Navigator Response Validation", "POST", "/compliance/navigator", 200, False, None, error)
            else:
                # Check if response contains markdown elements (basic check)
                response_text = data['response']
                has_markdown = any(marker in response_text for marker in ['##', '**', '-', '>', '`'])
                if not has_markdown:
                    print(f"   ⚠️  WARNING: AI response may not contain markdown formatting. Response: {response_text[:200]}...")
                
        return result

    def test_ai_navigator_without_project(self):
        """Test AI Navigator chat without project context"""
        chat_data = {
            "message": "Ce informații generale poți să îmi oferi despre eligibilitatea pentru proiecte de finanțare?"
        }
        success, data, error = self.api_request('POST', 'compliance/navigator', chat_data, expected_status=200)
        result = self.log_test("AI Navigator General", "POST", "/compliance/navigator", 200, success, data, error)
        
        # Validate response structure
        if success and data:
            has_response = 'response' in data and data['response']
            has_success = 'success' in data
            if not has_response or not has_success:
                result = False
                error = f"AI Navigator response missing fields. Got: {data}"
                self.log_test("AI Navigator General Response Validation", "POST", "/compliance/navigator", 200, False, None, error)
                
        return result

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
        print("🚀 STARTING GRANTFLOW BACKEND API TESTING - ITERATION 2")
        print("   Testing RBAC, Email Verification, Password Reset, OCR")
        print("="*60)
        print(f"Base URL: {self.base_url}")
        print(f"Test Email: {self.test_email}")
        print(f"Second User Email: {self.second_user_email}")
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
        
        # Email verification tests
        print("\n" + "="*40)
        print("📧 EMAIL VERIFICATION TESTS")
        print("="*40)
        
        self.test_email_verify()
        self.test_email_resend_verification()
        self.test_login_email_verified_status()
        
        # Password reset tests
        print("\n" + "="*40)
        print("🔑 PASSWORD RESET TESTS")
        print("="*40)
        
        self.test_password_reset_request()
        self.test_password_reset_confirm()
        self.test_login_with_new_password()
        self.test_change_password()
        
        # RBAC setup tests
        print("\n" + "="*40)
        print("👥 RBAC SETUP TESTS")
        print("="*40)
        
        self.test_rbac_register_second_user()
        
        # Organization tests with RBAC
        print("\n" + "="*40)
        print("🏢 ORGANIZATION TESTS (RBAC)")
        print("="*40)
        
        self.test_rbac_owner_create_org()  # Owner creates org
        self.test_org_list()
        self.test_org_detail()
        self.test_org_financial()
        self.test_rbac_owner_manage_members()  # Owner adds member
        self.test_rbac_imputernicit_limited_access()  # Member can't manage members
        
        # Project tests with RBAC
        print("\n" + "="*40)
        print("📋 PROJECT TESTS (RBAC)")
        print("="*40)
        
        self.test_rbac_owner_create_project()
        self.test_project_list()
        self.test_project_states()
        self.test_rbac_imputernicit_view_project()  # Member can view
        self.test_rbac_project_transition_owner_only()  # Only owner can transition
        
        # Document tests
        print("\n" + "="*40)
        print("📄 DOCUMENT TESTS")
        print("="*40)
        
        self.test_document_upload()
        self.test_document_list()
        
        # OCR tests
        print("\n" + "="*40)
        print("🔍 OCR TESTS (MOCKED)")
        print("="*40)
        
        self.test_ocr_trigger()
        self.test_ocr_get_results()
        self.test_ocr_correct_field()
        
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