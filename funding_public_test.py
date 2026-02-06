#!/usr/bin/env python3
import requests
import sys
import json

def test_funding_apis():
    """Test public funding APIs that don't require authentication"""
    base_url = "https://implementation-guide-1.preview.emergentagent.com/api"
    tests_run = 0
    tests_passed = 0
    
    def test_api(name, endpoint, expected_count=None, expected_fields=None):
        nonlocal tests_run, tests_passed
        tests_run += 1
        
        try:
            response = requests.get(f"{base_url}/{endpoint}", timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {name} - Status: {response.status_code}")
                
                # Validate count if specified
                if expected_count and isinstance(data, list):
                    if len(data) == expected_count:
                        print(f"   ✅ Count validation: {len(data)} items (expected {expected_count})")
                    else:
                        print(f"   ❌ Count validation: {len(data)} items (expected {expected_count})")
                        return
                
                # Validate fields if specified
                if expected_fields and isinstance(data, list) and len(data) > 0:
                    first_item = data[0]
                    missing_fields = [f for f in expected_fields if f not in first_item]
                    if not missing_fields:
                        print(f"   ✅ Fields validation: All required fields present")
                    else:
                        print(f"   ❌ Fields validation: Missing fields: {missing_fields}")
                        return
                
                # Show sample data
                if isinstance(data, list) and len(data) > 0:
                    print(f"   📄 Sample: {json.dumps(data[0], indent=2)[:200]}...")
                elif isinstance(data, dict):
                    print(f"   📄 Response: {json.dumps(data, indent=2)[:200]}...")
                
                tests_passed += 1
            else:
                print(f"❌ {name} - Status: {response.status_code}, Response: {response.text[:200]}")
                
        except Exception as e:
            print(f"❌ {name} - Error: {str(e)}")
    
    print("="*60)
    print("🚀 EU FUNDING MODULE - PUBLIC APIS TEST")
    print("="*60)
    print(f"Base URL: {base_url}")
    
    # Test programs (should return 4: PNRR, AFIR, POC, POR)
    test_api("Funding Programs", "funding/programs", expected_count=4, expected_fields=['id', 'denumire', 'masuri'])
    
    # Test SICAP search
    test_api("SICAP Search - Laptop", "funding/sicap/search?q=laptop", expected_fields=['cod', 'descriere', 'pret_referinta_min', 'pret_referinta_max'])
    
    # Test AFIR prices
    test_api("AFIR Prices - Tractor", "funding/afir/preturi?q=tractor", expected_fields=['categorie', 'subcategorie', 'pret_min', 'pret_max', 'unitate'])
    
    # Test templates (should return 8 templates)
    test_api("Draft Templates", "funding/templates", expected_count=8, expected_fields=['id', 'label', 'categorie', 'sectiuni'])
    
    # Test project types (should return 5 types)
    test_api("Project Types", "funding/project-types", expected_count=5, expected_fields=['id', 'label'])
    
    print("\n" + "="*60)
    print("📊 PUBLIC FUNDING APIS TEST SUMMARY")
    print("="*60)
    print(f"Tests Run: {tests_run}")
    print(f"Tests Passed: {tests_passed}")
    print(f"Tests Failed: {tests_run - tests_passed}")
    print(f"Success Rate: {(tests_passed/tests_run*100):.1f}%" if tests_run > 0 else "No tests run")
    
    return 0 if tests_passed == tests_run else 1

if __name__ == "__main__":
    exit_code = test_funding_apis()
    sys.exit(exit_code)