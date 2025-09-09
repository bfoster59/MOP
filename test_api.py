#!/usr/bin/env python3
"""
Test client for Gear Metrology API
Demonstrates API usage with example calculations
"""

import requests
import json
from typing import Dict, Any

# API base URL
BASE_URL = "http://localhost:8000"

def test_health():
    """Test the health endpoint"""
    print("=== Testing Health Endpoint ===")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print("✅ API is healthy")
            print(f"Version: {data['version']}")
            print("Features:")
            for feature in data['features']:
                print(f"  - {feature}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API. Make sure the server is running!")
        return False
    except Exception as e:
        print(f"❌ Error testing health: {e}")
        return False
    
    return True

def test_single_calculation():
    """Test single gear calculation"""
    print(f"\n=== Testing Single Calculation ===")
    
    # Test case: 127 teeth, 12 DP, 20° PA, 15° helix (previously problematic)
    test_request = {
        "teeth": 127,
        "diametral_pitch": 12.0,
        "pressure_angle": 20.0,
        "tooth_thickness": 0.130900,
        "helix_angle": 15.0,
        "is_internal": False,
        "is_metric": False,
        "use_best_pin": True
    }
    
    try:
        response = requests.post(f"{BASE_URL}/calculate", json=test_request)
        if response.status_code == 200:
            result = response.json()
            print("✅ Calculation successful")
            print(f"Gear: {test_request['teeth']} teeth, {test_request['helix_angle']}° helix")
            print(f"MOP: {result['measurement_value']:.6f} ± {result['uncertainty']:.6f} inches")
            print(f"Method: {result['method']}")
            print(f"Quality: {result['quality_rating']}")
            if result['helical_correction'] > 0:
                print(f"Helical correction: {result['helical_correction']:.6f} inches ({result['coefficient_set']})")
            if result['calculation_notes']:
                print("Notes:")
                for note in result['calculation_notes']:
                    print(f"  - {note}")
        else:
            print(f"❌ Calculation failed: {response.status_code}")
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"❌ Error testing calculation: {e}")

def test_batch_calculation():
    """Test batch calculations"""
    print(f"\n=== Testing Batch Calculations ===")
    
    # Test multiple helix angles that were previously problematic
    batch_request = {
        "calculations": [
            {
                "teeth": 127,
                "diametral_pitch": 12.0,
                "pressure_angle": 20.0,
                "tooth_thickness": 0.130900,
                "helix_angle": 5.0,  # Previously problematic
                "is_internal": False,
                "use_best_pin": True
            },
            {
                "teeth": 127,
                "diametral_pitch": 12.0,
                "pressure_angle": 20.0,
                "tooth_thickness": 0.130900,
                "helix_angle": 15.0,  # Previously problematic
                "is_internal": False,
                "use_best_pin": True
            },
            {
                "teeth": 45,
                "diametral_pitch": 8.0,
                "pressure_angle": 20.0,
                "tooth_thickness": 0.1963,
                "helix_angle": 20.0,
                "is_internal": False,
                "use_best_pin": True
            }
        ]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/batch", json=batch_request)
        if response.status_code == 200:
            result = response.json()
            print("✅ Batch calculation successful")
            print(f"Summary: {result['summary']['successful']}/{result['summary']['total_requested']} successful")
            print(f"Success rate: {result['summary']['success_rate']:.1f}%")
            
            print(f"\nResults:")
            for i, calc_result in enumerate(result['results']):
                params = calc_result['input_parameters']
                print(f"  {i+1}. {params['teeth']}T, {params['helix_angle']}° helix: {calc_result['measurement_value']:.6f} inches")
                
        else:
            print(f"❌ Batch calculation failed: {response.status_code}")
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"❌ Error testing batch: {e}")

def test_examples():
    """Test the examples endpoint"""
    print(f"\n=== Testing Examples Endpoint ===")
    
    try:
        response = requests.get(f"{BASE_URL}/examples")
        if response.status_code == 200:
            examples = response.json()
            print("✅ Examples endpoint working")
            print("Available examples:")
            for category, data in examples.items():
                print(f"  - {category}: {data['url']}")
        else:
            print(f"❌ Examples failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing examples: {e}")

def test_internal_gear():
    """Test internal gear calculation (MBP)"""
    print(f"\n=== Testing Internal Gear (MBP) ===")
    
    test_request = {
        "teeth": 127,
        "diametral_pitch": 12.0,
        "pressure_angle": 20.0,
        "tooth_thickness": 0.130900,  # Space width for internal
        "helix_angle": 10.5,
        "is_internal": True,
        "is_metric": False,
        "use_best_pin": True
    }
    
    try:
        response = requests.post(f"{BASE_URL}/calculate", json=test_request)
        if response.status_code == 200:
            result = response.json()
            print("✅ Internal gear calculation successful")
            print(f"MBP: {result['measurement_value']:.6f} ± {result['uncertainty']:.6f} inches")
            print(f"Type: {result['measurement_type']} using {result['method']} method")
            if result['helical_correction'] > 0:
                print(f"Helical correction: -{result['helical_correction']:.6f} inches (subtracted for internal)")
        else:
            print(f"❌ Internal calculation failed: {response.status_code}")
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"❌ Error testing internal gear: {e}")

def main():
    """Run all API tests"""
    print("🔧 Gear Metrology API Test Client")
    print("=" * 50)
    
    # Test if API is running
    if not test_health():
        print(f"\n💡 To start the API server, run:")
        print(f"   cd C:\\PROGRAMMING\\MOP")
        print(f"   python gear_api.py")
        print(f"\nOr start it manually with:")
        print(f"   uvicorn gear_api:app --reload --host 127.0.0.1 --port 8000")
        return
    
    # Run all tests
    test_single_calculation()
    test_batch_calculation()
    test_internal_gear()
    test_examples()
    
    print(f"\n=== Test Summary ===")
    print("✅ All tests completed!")
    print(f"🌐 API Documentation: {BASE_URL}/docs")
    print(f"📖 Alternative Docs: {BASE_URL}/redoc")
    print(f"🏠 Home Page: {BASE_URL}/")

if __name__ == "__main__":
    main()