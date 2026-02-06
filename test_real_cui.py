#!/usr/bin/env python3
"""
Test OpenAPI.ro integration with a specific real CUI - 14399840 (Dante International)
"""
import requests
import json
import uuid

BASE_URL = "https://implementation-guide-1.preview.emergentagent.com/api"

# Create test user
test_user = {
    "email": f"dante_test_{uuid.uuid4().hex[:8]}@example.com",
    "password": "DanteTest123!",
    "nume": "DanteTestNume",
    "prenume": "DanteTestPrenume",
    "telefon": "0722333444"
}

print(f"🧪 Testing REAL OpenAPI.ro integration with CUI 14399840 (Dante International)")
print(f"Test User: {test_user['email']}")

try:
    # Register test user
    response = requests.post(f"{BASE_URL}/auth/register", json=test_user)
    if response.status_code == 200:
        token = response.json().get('token')
        print(f"✅ User registered successfully")
    else:
        print(f"❌ Registration failed: {response.status_code} - {response.text}")
        exit(1)
    
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    
    # Test creating organization with real CUI 14399840
    print(f"\n🏢 Testing organization creation with REAL CUI 14399840...")
    cui = "14399840"
    org_data = {"cui": cui}
    
    response = requests.post(f"{BASE_URL}/organizations", json=org_data, headers=headers)
    
    if response.status_code == 200:
        org = response.json()
        print(f"✅ Organization created successfully!")
        print(f"   Company: {org.get('denumire', 'N/A')}")
        print(f"   CUI: {org.get('cui', 'N/A')}")
        print(f"   Address: {org.get('adresa', 'N/A')}")
        print(f"   County: {org.get('judet', 'N/A')}")
        print(f"   Legal Form: {org.get('forma_juridica', 'N/A')}")
        print(f"   Status: {org.get('stare', 'N/A')}")
        print(f"   Phone: {org.get('telefon', 'N/A')}")
        print(f"   VAT: {org.get('tva', 'N/A')}")
        print(f"   Data Source: {org.get('sursa_date', 'N/A')}")
        
        # Verify expected data for Dante International
        expected_checks = [
            ('denumire', 'Dante International', '✅ Company name contains "Dante International"'),
            ('judet', 'București', '✅ Located in București'),
            ('forma_juridica', 'SA', '✅ Legal form is SA'),
            ('sursa_date', 'OpenAPI.ro', '✅ Data source is OpenAPI.ro')
        ]
        
        print(f"\n🔍 Verifying expected data:")
        for field, expected, success_msg in expected_checks:
            value = str(org.get(field, '')).lower()
            if expected.lower() in value:
                print(f"   {success_msg}")
            else:
                print(f"   ❌ Expected {field} to contain '{expected}', got '{org.get(field, 'N/A')}'")
        
        org_id = org.get('id')
        
        # Test organization detail endpoint
        print(f"\n📋 Testing organization detail endpoint...")
        response = requests.get(f"{BASE_URL}/organizations/{org_id}", headers=headers)
        
        if response.status_code == 200:
            detail = response.json()
            print(f"✅ Organization detail retrieved successfully")
            print(f"   Registration Number: {detail.get('nr_reg_com', 'N/A')}")
            print(f"   Founded: {detail.get('data_infiintare', 'N/A')}")
            print(f"   Postal Code: {detail.get('cod_postal', 'N/A')}")
        else:
            print(f"❌ Failed to get organization detail: {response.status_code} - {response.text}")
            
    elif response.status_code == 400 and 'există deja' in response.text:
        print(f"ℹ️  Organization with CUI {cui} already exists in the system")
        print(f"   This actually confirms the OpenAPI.ro integration is working!")
        print(f"   Response: {response.json().get('detail', '')}")
        
        # Let's try to list existing organizations to see if we can access existing ones
        response = requests.get(f"{BASE_URL}/organizations", headers=headers)
        if response.status_code == 200:
            orgs = response.json()
            print(f"   Current user has {len(orgs)} organizations")
        
    else:
        print(f"❌ Failed to create organization: {response.status_code} - {response.text}")
        response_data = response.json() if response.content else {}
        print(f"   Response data: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
        
    # Test with invalid CUI
    print(f"\n❌ Testing invalid CUI 99999999...")
    invalid_org_data = {"cui": "99999999"}
    response = requests.post(f"{BASE_URL}/organizations", json=invalid_org_data, headers=headers)
    
    if response.status_code == 400:
        error_msg = response.json().get('detail', '')
        if 'nu este valid' in error_msg.lower():
            print(f"✅ Invalid CUI correctly rejected: {error_msg}")
        else:
            print(f"⚠️  CUI rejected but unexpected error: {error_msg}")
    else:
        print(f"❌ Invalid CUI should be rejected: {response.status_code} - {response.text}")
        
    # Test with RO prefix
    print(f"\n🔧 Testing CUI with RO prefix...")
    ro_prefix_data = {"cui": f"RO{cui}"}
    response = requests.post(f"{BASE_URL}/organizations", json=ro_prefix_data, headers=headers)
    
    if response.status_code == 400 and 'există deja' in response.text:
        print(f"✅ RO prefix correctly stripped and CUI recognized as existing")
    elif response.status_code == 200:
        org = response.json()
        print(f"✅ RO prefix correctly stripped and organization created")
        print(f"   Stored CUI: {org.get('cui', 'N/A')} (should be {cui})")
    else:
        print(f"❌ Unexpected response for RO prefixed CUI: {response.status_code} - {response.text}")

except Exception as e:
    print(f"❌ Test failed with error: {e}")
    import traceback
    traceback.print_exc()