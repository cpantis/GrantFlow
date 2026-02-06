#!/usr/bin/env python3
import requests
import sys
import json
import uuid
from datetime import datetime

class FundingModuleTest:
    def __init__(self):
        self.base_url = "https://implementation-guide-1.preview.emergentagent.com/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.org_id = None
        self.project_id = None
        
        # Test user data
        self.test_email = f"funding_test_{uuid.uuid4().hex[:8]}@example.com"
        self.test_password = "TestPass123!"
        self.test_user = {
            "email": self.test_email,
            "password": self.test_password,
            "nume": "FundingTestNume",
            "prenume": "FundingTestPrenume",
            "telefon": "0722123456"
        }

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
            print(f"   Response: {json.dumps(response_data, indent=2)[:300]}...")
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

    def setup_user_and_project(self):
        """Setup user, organization and project for funding tests"""
        # Register user
        success, data, error = self.api_request('POST', 'auth/register', self.test_user, expected_status=200)
        if success and data:
            self.token = data.get('token')
            print(f"✅ User registered successfully: {self.test_email}")
        else:
            print(f"❌ User registration failed: {error}")
            return False
        
        # Try to create organization, or get existing organizations
        unique_cui = f"1234567{uuid.uuid4().hex[:2]}"  # Generate unique CUI
        org_data = {"cui": unique_cui}
        success, data, error = self.api_request('POST', 'organizations', org_data, expected_status=200)
        if success and data:
            self.org_id = data.get('id')
            print(f"✅ Organization created successfully: {self.org_id}")
        else:
            # If creation failed, try to list existing organizations
            print(f"⚠️  Organization creation failed: {error}")
            print("   Trying to use existing organization...")
            success, data, error = self.api_request('GET', 'organizations', expected_status=200)
            if success and data and len(data) > 0:
                self.org_id = data[0].get('id')
                print(f"✅ Using existing organization: {self.org_id}")
            else:
                print(f"❌ Could not get any organization")
                return False
        
        # Create project
        project_data = {
            "titlu": f"EU Funding Test Project {uuid.uuid4().hex[:6]}",
            "organizatie_id": self.org_id,
            "program_finantare": "POC 2021-2027",
            "descriere": "Test project for EU Funding module validation",
            "buget_estimat": 200000,
            "obiective": ["Modernizare IT", "Digitalizare"]
        }
        success, data, error = self.api_request('POST', 'projects', project_data, expected_status=200)
        if success and data:
            self.project_id = data.get('id')
            print(f"✅ Project created successfully: {self.project_id}")
        else:
            print(f"❌ Project creation failed: {error}")
            return False
        
        return True

    def test_funding_programs(self):
        """Test get funding programs (PNRR, AFIR, POC, POR)"""
        success, data, error = self.api_request('GET', 'funding/programs', expected_status=200)
        result = self.log_test("Get Funding Programs", "GET", "/funding/programs", 200, success, data, error)
        
        if success and data:
            if not isinstance(data, list) or len(data) != 4:
                result = False
                error = f"Expected 4 programs, got {len(data) if isinstance(data, list) else 'non-list'}"
                self.log_test("Validate Programs Count", "GET", "/funding/programs", 200, False, None, error)
            else:
                program_ids = [p.get('id') for p in data]
                required_programs = ['pnrr', 'afir', 'poc', 'por']
                missing_programs = [p for p in required_programs if p not in program_ids]
                if missing_programs:
                    result = False
                    error = f"Missing programs: {missing_programs}"
                    self.log_test("Validate Required Programs", "GET", "/funding/programs", 200, False, None, error)
                
        return result

    def test_funding_sicap_search(self):
        """Test SICAP search for laptop"""
        success, data, error = self.api_request('GET', 'funding/sicap/search?q=laptop', expected_status=200)
        result = self.log_test("SICAP Search - Laptop", "GET", "/funding/sicap/search?q=laptop", 200, success, data, error)
        
        if success and data:
            if not isinstance(data, list):
                result = False
                error = "Expected list of CPV codes"
                self.log_test("Validate SICAP Response", "GET", "/funding/sicap/search", 200, False, None, error)
            elif len(data) > 0:
                first_item = data[0]
                required_fields = ['cod', 'descriere', 'pret_referinta_min', 'pret_referinta_max']
                missing_fields = [f for f in required_fields if f not in first_item]
                if missing_fields:
                    result = False
                    error = f"SICAP item missing fields: {missing_fields}"
                    self.log_test("Validate SICAP Item Structure", "GET", "/funding/sicap/search", 200, False, None, error)
                
        return result

    def test_funding_afir_search(self):
        """Test AFIR prices search for tractor"""
        success, data, error = self.api_request('GET', 'funding/afir/preturi?q=tractor', expected_status=200)
        result = self.log_test("AFIR Prices - Tractor", "GET", "/funding/afir/preturi?q=tractor", 200, success, data, error)
        
        if success and data:
            if not isinstance(data, list):
                result = False
                error = "Expected list of AFIR prices"
                self.log_test("Validate AFIR Response", "GET", "/funding/afir/preturi", 200, False, None, error)
            elif len(data) > 0:
                first_item = data[0]
                required_fields = ['categorie', 'subcategorie', 'pret_min', 'pret_max', 'unitate']
                missing_fields = [f for f in required_fields if f not in first_item]
                if missing_fields:
                    result = False
                    error = f"AFIR item missing fields: {missing_fields}"
                    self.log_test("Validate AFIR Item Structure", "GET", "/funding/afir/preturi", 200, False, None, error)
                
        return result

    def test_funding_templates(self):
        """Test get draft templates (should return 8 templates)"""
        success, data, error = self.api_request('GET', 'funding/templates', expected_status=200)
        result = self.log_test("Get Draft Templates", "GET", "/funding/templates", 200, success, data, error)
        
        if success and data:
            if not isinstance(data, list) or len(data) != 8:
                result = False
                error = f"Expected 8 templates, got {len(data) if isinstance(data, list) else 'non-list'}"
                self.log_test("Validate Templates Count", "GET", "/funding/templates", 200, False, None, error)
            else:
                first_template = data[0]
                required_fields = ['id', 'label', 'categorie', 'sectiuni']
                missing_fields = [f for f in required_fields if f not in first_template]
                if missing_fields:
                    result = False
                    error = f"Template missing fields: {missing_fields}"
                    self.log_test("Validate Template Structure", "GET", "/funding/templates", 200, False, None, error)
                
        return result

    def test_funding_project_types(self):
        """Test get project types (should return 5 types)"""
        success, data, error = self.api_request('GET', 'funding/project-types', expected_status=200)
        result = self.log_test("Get Project Types", "GET", "/funding/project-types", 200, success, data, error)
        
        if success and data:
            if not isinstance(data, list) or len(data) != 5:
                result = False
                error = f"Expected 5 project types, got {len(data) if isinstance(data, list) else 'non-list'}"
                self.log_test("Validate Project Types Count", "GET", "/funding/project-types", 200, False, None, error)
            else:
                type_ids = [t.get('id') for t in data]
                required_types = ['bunuri', 'bunuri_montaj', 'constructii', 'servicii', 'mixt']
                missing_types = [t for t in required_types if t not in type_ids]
                if missing_types:
                    result = False
                    error = f"Missing project types: {missing_types}"
                    self.log_test("Validate Required Project Types", "GET", "/funding/project-types", 200, False, None, error)
                
        return result

    def test_funding_project_config(self):
        """Test save project configuration"""
        config_data = {
            "project_id": self.project_id,
            "tip_proiect": "bunuri",
            "locatie_implementare": "Strada Test, nr. 123, București",
            "judet_implementare": "București",
            "tema_proiect": "Modernizarea infrastructurii IT prin achiziția de echipamente performante"
        }
        success, data, error = self.api_request('POST', 'funding/project-config', config_data, expected_status=200)
        result = self.log_test("Save Project Config", "POST", "/funding/project-config", 200, success, data, error)
        
        if success and data:
            has_config_fields = all(field in data for field in ['tip_proiect', 'locatie_implementare', 'judet_implementare', 'tema_proiect'])
            if not has_config_fields:
                result = False
                error = "Project config fields not saved properly"
                self.log_test("Validate Project Config Save", "POST", "/funding/project-config", 200, False, None, error)
                
        return result

    def test_funding_legislation_upload(self):
        """Test upload legislation file"""
        test_content = b"Ghidul Solicitantului - Test Content\nProcedura de evaluare si selectie\nCriterii de eligibilitate"
        files = {'file': ('ghid_test.txt', test_content, 'text/plain')}
        data = {
            'project_id': self.project_id,
            'titlu': 'Ghidul Solicitantului - Test',
            'tip': 'ghid'
        }
        
        success, response_data, error = self.api_request('POST', 'funding/legislation/upload', data=data, files=files, expected_status=200)
        result = self.log_test("Upload Legislation", "POST", "/funding/legislation/upload", 200, success, response_data, error)
        
        if success and response_data:
            required_fields = ['id', 'project_id', 'titlu', 'tip', 'filename', 'file_size']
            missing_fields = [f for f in required_fields if f not in response_data]
            if missing_fields:
                result = False
                error = f"Legislation upload response missing fields: {missing_fields}"
                self.log_test("Validate Legislation Upload Response", "POST", "/funding/legislation/upload", 200, False, None, error)
                
        return result

    def test_funding_generate_draft(self):
        """Test AI draft generation"""
        draft_data = {
            "project_id": self.project_id,
            "template_id": "plan_afaceri",
            "sectiune": "Rezumat executiv"
        }
        success, data, error = self.api_request('POST', 'funding/generate-draft', draft_data, expected_status=200)
        result = self.log_test("Generate Draft", "POST", "/funding/generate-draft", 200, success, data, error)
        
        if success and data:
            required_fields = ['id', 'project_id', 'template_id', 'template_label', 'continut', 'status', 'versiune']
            missing_fields = [f for f in required_fields if f not in data]
            if missing_fields:
                result = False
                error = f"Draft generation response missing fields: {missing_fields}"
                self.log_test("Validate Draft Generation Response", "POST", "/funding/generate-draft", 200, False, None, error)
            elif not data.get('continut'):
                result = False
                error = "Generated draft has no content"
                self.log_test("Validate Draft Content", "POST", "/funding/generate-draft", 200, False, None, error)
                
        return result

    def test_funding_evaluate_conformity(self):
        """Test conformity evaluation agent"""
        eval_data = {"project_id": self.project_id}
        success, data, error = self.api_request('POST', 'funding/evaluate-conformity', eval_data, expected_status=200)
        result = self.log_test("Evaluate Conformity", "POST", "/funding/evaluate-conformity", 200, success, data, error)
        
        if success and data:
            required_fields = ['id', 'project_id', 'type', 'result', 'success']
            missing_fields = [f for f in required_fields if f not in data]
            if missing_fields:
                result = False
                error = f"Conformity evaluation response missing fields: {missing_fields}"
                self.log_test("Validate Conformity Response", "POST", "/funding/evaluate-conformity", 200, False, None, error)
            elif not data.get('result'):
                result = False
                error = "Conformity evaluation has no result"
                self.log_test("Validate Conformity Result", "POST", "/funding/evaluate-conformity", 200, False, None, error)
                
        return result

    def run_funding_tests(self):
        """Run focused EU Funding Module tests"""
        print("="*60)
        print("🚀 EU FUNDING MODULE - FOCUSED TESTING")
        print("   Programs → Measures → Sessions + SICAP + AFIR + AI")
        print("="*60)
        print(f"Base URL: {self.base_url}")
        print(f"Test Date: {datetime.now().isoformat()}")
        
        # Setup
        print("\n" + "="*40)
        print("⚙️  SETUP: User + Organization + Project")
        print("="*40)
        
        if not self.setup_user_and_project():
            print("❌ Setup failed - stopping tests")
            return self.print_summary()
        
        # Funding Module tests
        print("\n" + "="*40)
        print("💰 EU FUNDING MODULE TESTS")
        print("="*40)
        
        self.test_funding_programs()
        self.test_funding_sicap_search()
        self.test_funding_afir_search()
        self.test_funding_templates()
        self.test_funding_project_types()
        self.test_funding_project_config()
        self.test_funding_legislation_upload()
        self.test_funding_generate_draft()
        self.test_funding_evaluate_conformity()
        
        return self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("📊 EU FUNDING MODULE TEST SUMMARY")
        print("="*60)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "No tests run")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL EU FUNDING MODULE TESTS PASSED!")
            return 0
        else:
            print("⚠️  SOME EU FUNDING MODULE TESTS FAILED")
            return 1

if __name__ == "__main__":
    tester = FundingModuleTest()
    exit_code = tester.run_funding_tests()
    sys.exit(exit_code)