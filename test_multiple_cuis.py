#!/usr/bin/env python3
"""
Test OpenAPI.ro with multiple real CUIs to find one that works
"""
import requests
import json
import uuid

BASE_URL = "https://implementation-guide-1.preview.emergentagent.com/api"

# Create test user
test_user = {
    "email": f"multi_cui_test_{uuid.uuid4().hex[:8]}@example.com",
    "password": "MultiCUITest123!",
    "nume": "MultiTestNume",
    "prenume": "MultiTestPrenume",
    "telefon": "0722555666"
}

# Real CUIs to try (some alternative ones)
test_cuis = [
    "16462378",  # Another real CUI
    "17196441",  # Another real CUI
    "22675362",  # Another real CUI
    "33034700",  # Termene Just SRL (from requirements)
    "14399840",  # Dante International (from requirements)
]

print(f"🧪 Testing OpenAPI.ro with multiple real CUIs")
print(f"Test User: {test_user['email']}")
print(f"Testing CUIs: {test_cuis}")

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
    
    successful_creations = []
    
    for cui in test_cuis:
        print(f"\n🏢 Testing CUI {cui}...")
        org_data = {"cui": cui}
        
        response = requests.post(f"{BASE_URL}/organizations", json=org_data, headers=headers)
        
        if response.status_code == 200:
            org = response.json()
            successful_creations.append(cui)
            print(f"✅ SUCCESS: Organization created for CUI {cui}")
            print(f"   Company: {org.get('denumire', 'N/A')}")
            print(f"   Address: {org.get('adresa', 'N/A')}")
            print(f"   County: {org.get('judet', 'N/A')}")
            print(f"   Legal Form: {org.get('forma_juridica', 'N/A')}")
            print(f"   Status: {org.get('stare', 'N/A')}")
            print(f"   Data Source: {org.get('sursa_date', 'N/A')}")
            
            if org.get('sursa_date') == 'OpenAPI.ro':
                print(f"   ✅ Correct OpenAPI.ro data source!")
            else:
                print(f"   ❌ Wrong data source: {org.get('sursa_date', 'N/A')}")
                
        elif response.status_code == 400:
            error = response.json().get('detail', '')
            if 'există deja' in error:
                print(f"ℹ️  CUI {cui} already exists - OpenAPI.ro working!")
            elif 'nu este valid' in error:
                print(f"❌ CUI {cui} reported as invalid: {error}")
            else:
                print(f"❌ CUI {cui} failed: {error}")
        else:
            print(f"❌ CUI {cui} failed: {response.status_code} - {response.text}")
    
    print(f"\n📊 Results Summary:")
    print(f"Successfully created organizations: {len(successful_creations)}")
    if successful_creations:
        print(f"CUIs that worked: {successful_creations}")
        
        # Test organization listing
        response = requests.get(f"{BASE_URL}/organizations", headers=headers)
        if response.status_code == 200:
            orgs = response.json()
            print(f"\nUser now has {len(orgs)} organizations:")
            for org in orgs:
                print(f"  - {org.get('denumire', 'N/A')} (CUI: {org.get('cui', 'N/A')}, Source: {org.get('sursa_date', 'N/A')})")
    else:
        print(f"No new organizations created (all may already exist)")
        
    # Final test: invalid CUI
    print(f"\n❌ Final test with invalid CUI...")
    response = requests.post(f"{BASE_URL}/organizations", json={"cui": "99999999"}, headers=headers)
    if response.status_code == 400:
        error = response.json().get('detail', '')
        if 'nu este valid' in error:
            print(f"✅ Invalid CUI correctly rejected: {error}")
        else:
            print(f"⚠️  CUI rejected but unexpected error: {error}")
    else:
        print(f"❌ Invalid CUI should be rejected: {response.status_code}")

except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()