#!/usr/bin/env python3
"""
Check existing organizations for OpenAPI.ro real data
"""
import requests
import json

BASE_URL = "https://implementation-guide-1.preview.emergentagent.com/api"

# First register and login to get a token
test_user = {
    "email": "quick_check@example.com",
    "password": "QuickCheck123!",
    "nume": "QuickTestNume",
    "prenume": "QuickTestPrenume",
    "telefon": "0722111222"
}

# Register
try:
    response = requests.post(f"{BASE_URL}/auth/register", json=test_user)
    if response.status_code == 200:
        token = response.json().get('token')
        print(f"✅ Registered successfully, got token")
    else:
        # Try login instead
        login_data = {"email": test_user["email"], "password": test_user["password"]}
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        if response.status_code == 200:
            token = response.json().get('token')
            print(f"✅ Logged in successfully, got token")
        else:
            print(f"❌ Failed to get token: {response.status_code} {response.text}")
            exit(1)
    
    # Get organizations
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    response = requests.get(f"{BASE_URL}/organizations", headers=headers)
    
    if response.status_code == 200:
        orgs = response.json()
        print(f"\n📋 Found {len(orgs)} organizations in the system:")
        
        # Check for our specific real CUIs
        target_cuis = ["14399840", "33034700", "18189442"]
        
        for org in orgs:
            cui = org.get('cui', '')
            name = org.get('denumire', 'N/A')
            source = org.get('sursa_date', 'N/A')
            address = org.get('adresa', 'N/A')
            judet = org.get('judet', 'N/A')
            forma_juridica = org.get('forma_juridica', 'N/A')
            
            print(f"\n🏢 {name}")
            print(f"   CUI: {cui}")
            print(f"   Source: {source}")
            print(f"   Address: {address}")
            print(f"   Judet: {judet}")
            print(f"   Forma juridica: {forma_juridica}")
            
            if cui in target_cuis:
                print(f"   ✅ FOUND TARGET CUI {cui}!")
                if source == 'OpenAPI.ro':
                    print(f"   ✅ Has correct OpenAPI.ro source")
                else:
                    print(f"   ❌ Wrong source: expected 'OpenAPI.ro', got '{source}'")
    else:
        print(f"❌ Failed to get organizations: {response.status_code} {response.text}")
        
    # Try creating one with a new unique CUI to test the integration
    print(f"\n🧪 Testing OpenAPI.ro integration with a new unique CUI...")
    unique_cui = "99999998"  # This should fail
    
    response = requests.post(f"{BASE_URL}/organizations", 
                           json={"cui": unique_cui}, 
                           headers=headers)
    
    if response.status_code == 400:
        error = response.json().get('detail', '')
        print(f"✅ Invalid CUI correctly rejected: {error}")
    else:
        print(f"❌ Unexpected response for invalid CUI: {response.status_code} {response.text}")

except Exception as e:
    print(f"❌ Error: {e}")