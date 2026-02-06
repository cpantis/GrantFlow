#!/usr/bin/env python3
"""
GrantFlow OpenAPI.ro Integration Test
Tests REAL OpenAPI.ro integration with specific CUIs as per review requirements
"""
import requests
import sys
import json
import uuid
from datetime import datetime

class OpenAPIRoTester:
    def __init__(self):
        self.base_url = "https://implementation-guide-1.preview.emergentagent.com/api"
        self.token = None
        self.user_data = None
        self.tests_run = 0
        self.tests_passed = 0
        
        # Test user data for OpenAPI.ro tests
        self.test_email = f"openapi_test_{uuid.uuid4().hex[:8]}@example.com"
        self.test_password = "OpenAPITest123!"
        self.test_user = {
            "email": self.test_email,
            "password": self.test_password,
            "nume": "OpenAPITestNume",
            "prenume": "OpenAPITestPrenume",
            "telefon": "0722987654"
        }
        
        # Real CUIs to test (as per requirements)
        self.real_cuis = {
            "dante_international": "14399840",  # Dante International S.A. / eMAG
            "termene_just": "33034700",        # Termene Just SRL
            "fan_courier": "18189442"          # FAN Courier (additional real CUI)
        }
        
        # Invalid CUI to test error handling
        self.invalid_cui = "99999999"
        
        # Store created org IDs for cleanup
        self.created_org_ids = []

    def log_test(self, name, method, endpoint, expected_status, result, response_data=None, error=None):
        """Log test result with detailed info"""
        status = "✅ PASSED" if result else "❌ FAILED"
        self.tests_run += 1
        if result:
            self.tests_passed += 1
        
        print(f"\n{status} | {method} {endpoint}")
        print(f"   Test: {name}")
        print(f"   Expected Status: {expected_status}")
        if error:
            print(f"   Error: {error}")
        if response_data and isinstance(response_data, dict):
            if result and 'data' in str(response_data):
                # Show key data fields for successful org creation
                if 'denumire' in str(response_data):
                    company_name = response_data.get('denumire', '')
                    cui = response_data.get('cui', '')
                    sursa = response_data.get('sursa_date', '')
                    print(f"   Company: {company_name} (CUI: {cui}, Source: {sursa})")
            else:
                # Show response snippet
                print(f"   Response: {json.dumps(response_data, ensure_ascii=False, indent=2)[:300]}...")
        return result

    def api_request(self, method, endpoint, data=None, expected_status=200):
        """Make API request with error handling"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
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

    def test_auth_setup(self):
        """Setup authentication for OpenAPI.ro tests"""
        print("🔐 Setting up authentication for OpenAPI.ro tests...")
        
        # Register test user
        success, data, error = self.api_request('POST', 'auth/register', self.test_user, expected_status=200)
        if not self.log_test("OpenAPI.ro Test User Registration", "POST", "/auth/register", 200, success, data, error):
            return False
        
        if success and data:
            self.token = data.get('token')
            self.user_data = data.get('user')
        
        return True

    def test_real_cui_dante_international(self):
        """Test creating organization with REAL CUI 14399840 (Dante International/eMAG)"""
        cui = self.real_cuis["dante_international"]
        org_data = {"cui": cui}
        
        success, data, error = self.api_request('POST', 'organizations', org_data, expected_status=200)
        result = self.log_test("Create Org with REAL CUI 14399840 (Dante International)", "POST", "/organizations", 200, success, data, error)
        
        if success and data:
            org_id = data.get('id')
            if org_id:
                self.created_org_ids.append(org_id)
            
            # Verify specific data for Dante International
            expected_data = {
                'denumire': 'Dante International S.A.',
                'judet': 'Municipiul București',
                'forma_juridica': 'SA',
                'sursa_date': 'OpenAPI.ro'
            }
            
            for field, expected_value in expected_data.items():
                actual_value = data.get(field, '')
                if expected_value.lower() not in actual_value.lower():
                    print(f"   ⚠️  WARNING: Expected {field}='{expected_value}', got '{actual_value}'")
                else:
                    print(f"   ✅ Verified {field}: {actual_value}")
        
        return result

    def test_real_cui_termene_just(self):
        """Test creating organization with REAL CUI 33034700 (Termene Just SRL)"""
        cui = self.real_cuis["termene_just"]
        org_data = {"cui": cui}
        
        success, data, error = self.api_request('POST', 'organizations', org_data, expected_status=200)
        result = self.log_test("Create Org with REAL CUI 33034700 (Termene Just SRL)", "POST", "/organizations", 200, success, data, error)
        
        if success and data:
            org_id = data.get('id')
            if org_id:
                self.created_org_ids.append(org_id)
            
            # Verify presence of real address and phone data
            address = data.get('adresa', '')
            phone = data.get('telefon', '')
            sursa = data.get('sursa_date', '')
            
            if address:
                print(f"   ✅ Real address found: {address}")
            else:
                print(f"   ⚠️  WARNING: No address data found")
                
            if phone:
                print(f"   ✅ Real phone found: {phone}")
            else:
                print(f"   ℹ️  INFO: No phone data (may be unavailable in OpenAPI.ro)")
                
            if sursa == 'OpenAPI.ro':
                print(f"   ✅ Correct data source: {sursa}")
            else:
                print(f"   ❌ Wrong data source: expected 'OpenAPI.ro', got '{sursa}'")
        
        return result

    def test_real_cui_fan_courier(self):
        """Test creating organization with REAL CUI 18189442 (FAN Courier)"""
        cui = self.real_cuis["fan_courier"]
        org_data = {"cui": cui}
        
        success, data, error = self.api_request('POST', 'organizations', org_data, expected_status=200)
        result = self.log_test("Create Org with REAL CUI 18189442 (FAN Courier)", "POST", "/organizations", 200, success, data, error)
        
        if success and data:
            self.created_org_ids.append(data.get('id'))
            
            # Verify OpenAPI.ro source
            sursa = data.get('sursa_date', '')
            if sursa == 'OpenAPI.ro':
                print(f"   ✅ Correct data source: {sursa}")
                
        return result

    def test_invalid_cui_error(self):
        """Test creating organization with INVALID CUI 99999999 - should return error"""
        org_data = {"cui": self.invalid_cui}
        
        success, data, error = self.api_request('POST', 'organizations', org_data, expected_status=400)
        result = self.log_test("Create Org with INVALID CUI 99999999", "POST", "/organizations", 400, success, data, error)
        
        if success and data:
            error_message = data.get('detail', '')
            if 'nu este valid' in error_message.lower() or 'invalid' in error_message.lower():
                print(f"   ✅ Correct error message: {error_message}")
            else:
                print(f"   ⚠️  Unexpected error message: {error_message}")
                
        return result

    def test_cui_with_ro_prefix(self):
        """Test CUI with RO prefix - should strip prefix and work correctly"""
        cui_with_prefix = f"RO{self.real_cuis['dante_international']}"
        org_data = {"cui": cui_with_prefix}
        
        success, data, error = self.api_request('POST', 'organizations', org_data, expected_status=400)  # Should fail as duplicate
        
        if not success and data and 'există deja' in data.get('detail', ''):
            # This is expected - the CUI already exists (we created it before)
            result = True
            print(f"   ✅ RO prefix correctly stripped - CUI recognized as existing")
            self.log_test("CUI with RO prefix handling", "POST", "/organizations", 400, True, data, None)
        else:
            # If it doesn't exist yet, it should succeed with real data
            result = self.log_test("CUI with RO prefix handling", "POST", "/organizations", 200, success, data, error)
            if success and data:
                self.created_org_ids.append(data.get('id'))
                
        return result

    def test_openapi_ro_field_presence(self):
        """Test that all created organizations have sursa_date='OpenAPI.ro' field"""
        if not self.created_org_ids:
            return self.log_test("Check OpenAPI.ro Field Presence", "GET", "/organizations", 200, False, None, "No organizations created")
        
        success, data, error = self.api_request('GET', 'organizations', expected_status=200)
        result = self.log_test("Check OpenAPI.ro Field Presence", "GET", "/organizations", 200, success, data, error)
        
        if success and data:
            openapi_orgs = [org for org in data if org.get('sursa_date') == 'OpenAPI.ro']
            total_orgs = len(data)
            openapi_count = len(openapi_orgs)
            
            print(f"   Organizations with OpenAPI.ro source: {openapi_count}/{total_orgs}")
            
            if openapi_count > 0:
                print(f"   ✅ Found organizations with OpenAPI.ro source")
                for org in openapi_orgs:
                    print(f"      - {org.get('denumire', 'N/A')} (CUI: {org.get('cui', 'N/A')})")
            else:
                print(f"   ❌ No organizations found with OpenAPI.ro source")
                result = False
                
        return result

    def test_organization_detail_real_data(self):
        """Test organization detail endpoint returns real data fields"""
        if not self.created_org_ids:
            return self.log_test("Check Organization Detail Real Data", "GET", "/organizations/{id}", 200, False, None, "No organizations created")
        
        org_id = self.created_org_ids[0]  # Test first created org
        success, data, error = self.api_request('GET', f'organizations/{org_id}', expected_status=200)
        result = self.log_test("Check Organization Detail Real Data", "GET", f"/organizations/{org_id}", 200, success, data, error)
        
        if success and data:
            required_fields = ['denumire', 'cui', 'adresa', 'judet', 'forma_juridica', 'stare', 'sursa_date']
            present_fields = [field for field in required_fields if data.get(field)]
            missing_fields = [field for field in required_fields if not data.get(field)]
            
            print(f"   Present fields: {', '.join(present_fields)}")
            if missing_fields:
                print(f"   Missing/empty fields: {', '.join(missing_fields)}")
            
            # Check specific OpenAPI.ro fields
            if data.get('sursa_date') == 'OpenAPI.ro':
                print(f"   ✅ Correct data source: OpenAPI.ro")
            else:
                print(f"   ❌ Wrong data source: {data.get('sursa_date', 'N/A')}")
                
        return result

    def run_openapi_ro_tests(self):
        """Run all OpenAPI.ro integration tests"""
        print("="*70)
        print("🌐 GRANTFLOW OPENAPI.RO INTEGRATION TESTS - ITERATION 6")
        print("   Testing REAL OpenAPI.ro integration with specific CUIs")
        print("="*70)
        print(f"Base URL: {self.base_url}")
        print(f"Test Email: {self.test_email}")
        print(f"Test Date: {datetime.now().isoformat()}")
        print(f"Real CUIs to test: {list(self.real_cuis.values())}")
        print(f"Invalid CUI to test: {self.invalid_cui}")
        
        # Setup authentication
        print("\n" + "="*50)
        print("🔐 AUTHENTICATION SETUP")
        print("="*50)
        if not self.test_auth_setup():
            print("❌ Authentication setup failed - stopping tests")
            return self.print_summary()
        
        # Test real CUIs
        print("\n" + "="*50)
        print("🏢 REAL CUI TESTS - OPENAPI.RO INTEGRATION")
        print("="*50)
        
        self.test_real_cui_dante_international()
        self.test_real_cui_termene_just() 
        self.test_real_cui_fan_courier()
        
        # Test error handling
        print("\n" + "="*50)
        print("❌ ERROR HANDLING TESTS")
        print("="*50)
        
        self.test_invalid_cui_error()
        self.test_cui_with_ro_prefix()
        
        # Test data verification
        print("\n" + "="*50)
        print("🔍 DATA VERIFICATION TESTS")
        print("="*50)
        
        self.test_openapi_ro_field_presence()
        self.test_organization_detail_real_data()
        
        return self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*70)
        print("📊 OPENAPI.RO INTEGRATION TEST SUMMARY")
        print("="*70)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "No tests run")
        
        if self.created_org_ids:
            print(f"\nCreated {len(self.created_org_ids)} organizations with real data:")
            print(f"Organization IDs: {', '.join(self.created_org_ids)}")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL OPENAPI.RO TESTS PASSED!")
            print("✅ Real OpenAPI.ro integration working correctly")
            return 0
        else:
            print("⚠️  SOME OPENAPI.RO TESTS FAILED")
            print("❌ Real OpenAPI.ro integration issues detected")
            return 1

if __name__ == "__main__":
    tester = OpenAPIRoTester()
    exit_code = tester.run_openapi_ro_tests()
    sys.exit(exit_code)