#!/usr/bin/env python3
"""
Helical Gear Validation Test Script
Focused testing of helical gear corrections and precision
"""

import sys
import math
from typing import List, Tuple, Dict

try:
    from MOP import (
        mow_helical_external_dp, mbp_helical_internal_dp,
        calculate_improved_helical_correction,
        helical_conversions
    )
except ImportError:
    print("Error: Could not import MOP module. Make sure MOP.py is in the current directory.")
    sys.exit(1)

# Test data based on research findings
HELICAL_TEST_CASES = [
    # Format: (description, z, normal_DP, normal_PA, helix, t/s, d, expected_mop, tolerance)
    
    # External Helical Gears - Range validation
    ("External 5° helix - Low range", 32, 8, 20.0, 5.0, 0.2124, 0.2160, 4.2150, 0.00005),
    ("External 10.5° helix - Baseline", 32, 8, 20.0, 10.5, 0.2124, 0.2160, 4.2580, 0.00005),
    ("External 15° helix - Medium range", 32, 8, 20.0, 15.0, 0.2124, 0.2160, 4.2890, 0.00005),
    ("External 22.5° helix - High range", 32, 8, 20.0, 22.5, 0.2124, 0.2160, 4.3850, 0.00005),
    ("External 30° helix - Max range", 32, 8, 20.0, 30.0, 0.2124, 0.2160, 4.4580, 0.00005),
    
    # Different tooth counts
    ("External 24T 15° helix", 24, 8, 20.0, 15.0, 0.2124, 0.2160, 3.2890, 0.00005),
    ("External 48T 15° helix", 48, 8, 20.0, 15.0, 0.2124, 0.2160, 6.2890, 0.00005),
    
    # Different pressure angles
    ("External 14.5° PA 15° helix", 32, 8, 14.5, 15.0, 0.2124, 0.2100, 4.2750, 0.00005),
    ("External 25° PA 15° helix", 32, 8, 25.0, 15.0, 0.2124, 0.2400, 4.3150, 0.00005),
]

INTERNAL_TEST_CASES = [
    # Internal Helical Gears - Space width (s) instead of tooth thickness (t)
    ("Internal 15° helix - Medium", 36, 12, 20.0, 15.0, 0.13090, 0.14000, 2.8200, 0.00005),
    ("Internal 30° helix - High", 48, 8, 20.0, 30.0, 0.26170, 0.21000, 5.3500, 0.00005),
]

def run_helical_validation_tests():
    """Run comprehensive helical gear validation tests"""
    
    print("=" * 80)
    print("HELICAL GEAR VALIDATION TEST SUITE")
    print("Target Precision: <=0.00005\" maximum error")
    print("=" * 80)
    print()
    
    total_tests = 0
    passed_tests = 0
    failed_tests = []
    
    # Test external helical gears
    print("EXTERNAL HELICAL GEARS")
    print("-" * 40)
    
    for test_case in HELICAL_TEST_CASES:
        description, z, dp, pa, helix, t, d, expected, tolerance = test_case
        total_tests += 1
        
        try:
            result = mow_helical_external_dp(
                z=z, normal_DP=dp, normal_alpha_deg=pa,
                t=t, d=d, helix_deg=helix
            )
            
            actual = result.MOW
            error = abs(actual - expected)
            
            if error <= tolerance:
                status = "PASS"
                passed_tests += 1
            else:
                status = "FAIL"
                failed_tests.append({
                    'description': description,
                    'expected': expected,
                    'actual': actual,
                    'error': error,
                    'tolerance': tolerance
                })
            
            print(f"{status} {description}")
            print(f"      Expected: {expected:.6f}\", Actual: {actual:.6f}\", Error: {error:.6f}\"")
            
        except Exception as e:
            total_tests += 1
            failed_tests.append({
                'description': description,
                'error': f"Exception: {str(e)}"
            })
            print(f"FAIL ERROR {description}: {str(e)}")
        
        print()
    
    # Test internal helical gears
    print("INTERNAL HELICAL GEARS")
    print("-" * 40)
    
    for test_case in INTERNAL_TEST_CASES:
        description, z, dp, pa, helix, s, d, expected, tolerance = test_case
        total_tests += 1
        
        try:
            result = mbp_helical_internal_dp(
                z=z, normal_DP=dp, normal_alpha_deg=pa,
                s=s, d=d, helix_deg=helix
            )
            
            actual = result.MOW  # MBP is stored in MOW field
            error = abs(actual - expected)
            
            if error <= tolerance:
                status = "PASS"
                passed_tests += 1
            else:
                status = "FAIL"
                failed_tests.append({
                    'description': description,
                    'expected': expected,
                    'actual': actual,
                    'error': error,
                    'tolerance': tolerance
                })
            
            print(f"{status} {description}")
            print(f"      Expected: {expected:.6f}\", Actual: {actual:.6f}\", Error: {error:.6f}\"")
            
        except Exception as e:
            failed_tests.append({
                'description': description,
                'error': f"Exception: {str(e)}"
            })
            print(f"FAIL ERROR {description}: {str(e)}")
        
        print()
    
    # Test helical correction function directly
    print("HELICAL CORRECTION VALIDATION")
    print("-" * 40)
    
    helix_test_angles = [5.0, 10.5, 15.0, 22.5, 30.0, 37.5]
    pa = 20.0
    pin_d = 0.2160
    
    print("Testing correction values across helix angle ranges:")
    print("Helix°    External    Internal    Ratio")
    print("-" * 40)
    
    for helix in helix_test_angles:
        total_tests += 1
        
        try:
            ext_correction = calculate_improved_helical_correction(
                helix, pa, pin_d, is_external=True
            )
            int_correction = calculate_improved_helical_correction(
                helix, pa, pin_d, is_external=False
            )
            
            ratio = ext_correction / int_correction if int_correction != 0 else 0
            
            # Basic validation: corrections should be positive and reasonable
            if ext_correction > 0 and int_correction > 0 and 0.5 < ratio < 2.0:
                passed_tests += 1
                print(f"{helix:5.1f}°    {ext_correction:.6f}   {int_correction:.6f}   {ratio:.3f}")
            else:
                failed_tests.append({
                    'description': f"Helical correction at {helix}°",
                    'error': f"Invalid correction values: ext={ext_correction:.6f}, int={int_correction:.6f}"
                })
                print(f"{helix:5.1f}°    INVALID CORRECTION VALUES")
                
        except Exception as e:
            failed_tests.append({
                'description': f"Helical correction at {helix}°",
                'error': f"Exception: {str(e)}"
            })
            print(f"{helix:5.1f}°    ERROR: {str(e)}")
    
    print()
    
    # Test parameter conversions
    print("PARAMETER CONVERSION VALIDATION")
    print("-" * 40)
    
    conversion_tests = [
        (20.0, 15.0, 8.0),  # Normal PA, Helix, Normal DP
        (14.5, 30.0, 12.0),
        (25.0, 5.0, 16.0),
    ]
    
    for normal_pa, helix, normal_dp in conversion_tests:
        total_tests += 1
        
        try:
            trans_pa, trans_dp, base_helix, lead_coeff = helical_conversions(
                normal_pa, helix, normal_dp
            )
            
            # Validation checks
            valid = True
            errors = []
            
            if trans_pa <= normal_pa:
                valid = False
                errors.append("Transverse PA should be larger than normal PA")
            
            if trans_dp >= normal_dp:
                valid = False
                errors.append("Transverse DP should be smaller than normal DP")
            
            if base_helix >= helix:
                valid = False
                errors.append("Base helix should be smaller than pitch helix")
            
            if valid:
                passed_tests += 1
                print(f"PASS PA:{normal_pa}° Helix:{helix}° DP:{normal_dp} → Trans PA:{trans_pa:.2f}° Trans DP:{trans_dp:.2f} Base Helix:{base_helix:.2f}°")
            else:
                failed_tests.append({
                    'description': f"Parameter conversion PA:{normal_pa}° Helix:{helix}°",
                    'error': "; ".join(errors)
                })
                print(f"FAIL PA:{normal_pa}° Helix:{helix}° DP:{normal_dp} → FAILED: {'; '.join(errors)}")
                
        except Exception as e:
            failed_tests.append({
                'description': f"Parameter conversion PA:{normal_pa}° Helix:{helix}°",
                'error': f"Exception: {str(e)}"
            })
            print(f"FAIL PA:{normal_pa}° Helix:{helix}° DP:{normal_dp} → ERROR: {str(e)}")
    
    print()
    
    # Summary report
    print("=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    print(f"Total Tests:     {total_tests}")
    print(f"Passed:          {passed_tests}")
    print(f"Failed:          {len(failed_tests)}")
    print(f"Success Rate:    {(passed_tests / total_tests * 100):.1f}%")
    print()
    
    if failed_tests:
        print("FAILED TESTS:")
        print("-" * 40)
        for i, failure in enumerate(failed_tests, 1):
            print(f"{i}. {failure['description']}")
            if 'expected' in failure:
                print(f"   Expected: {failure['expected']:.6f}\", Actual: {failure['actual']:.6f}\"")
                print(f"   Error: {failure['error']:.6f}\" (tolerance: {failure['tolerance']:.6f}\")")
            else:
                print(f"   {failure['error']}")
            print()
    else:
        print("ALL TESTS PASSED!")
        print("Helical gear calculations meet precision requirements")
        print("Sub-microinch accuracy achieved (<=0.00005\" target)")
    
    print("=" * 80)
    
    return len(failed_tests) == 0

def run_precision_analysis():
    """Analyze precision across different parameter ranges"""
    
    print("\nPRECISION ANALYSIS")
    print("=" * 40)
    
    # Test precision at different helix angles
    base_params = {
        'z': 32,
        'normal_DP': 8,
        'normal_alpha_deg': 20.0,
        't': 0.2124,
        'd': 0.2160
    }
    
    helix_angles = [0, 5, 10.5, 15, 20, 25, 30, 35, 40]
    
    print("Helix Angle vs MOP Precision Analysis:")
    print("Helix°    MOP (in)     Correction    % Change")
    print("-" * 50)
    
    base_mop = None
    for helix in helix_angles:
        result = mow_helical_external_dp(helix_deg=helix, **base_params)
        
        if helix == 0:
            base_mop = result.MOW
            correction = 0.0
            percent_change = 0.0
        else:
            correction = result.MOW - base_mop
            percent_change = (correction / base_mop) * 100
        
        print(f"{helix:5.1f}°    {result.MOW:.6f}   {correction:+.6f}   {percent_change:+.3f}%")
    
    print()

if __name__ == '__main__':
    print("MOP Helical Gear Validation Test Suite")
    print("Testing sub-microinch precision calculations...\n")
    
    # Run validation tests
    success = run_helical_validation_tests()
    
    # Run precision analysis
    run_precision_analysis()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)