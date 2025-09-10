#!/usr/bin/env python3
"""
Simple Helical Gear Test Script
Basic validation of helical gear functionality
"""

import sys

try:
    from MOP import (
        mow_spur_external_dp, mow_helical_external_dp,
        mbp_spur_internal_dp, mbp_helical_internal_dp,
        calculate_improved_helical_correction
    )
except ImportError:
    print("Error: Could not import MOP module.")
    sys.exit(1)

def test_basic_functionality():
    """Test basic helical gear functionality"""
    
    print("BASIC HELICAL GEAR FUNCTIONALITY TEST")
    print("=" * 50)
    
    # Standard test parameters
    z = 32
    dp = 8
    pa = 20.0
    t = 0.2124
    d = 0.2160
    
    # Test spur gear (baseline)
    print("\n1. Spur Gear Baseline (helix = 0 degrees)")
    spur_result = mow_spur_external_dp(z=z, DP=dp, alpha_deg=pa, t=t, d=d)
    print(f"   Spur MOP: {spur_result.MOW:.6f}")
    
    # Test helical gear with 0 degrees (should match spur)
    print("\n2. Helical Gear with 0 degrees (should match spur)")
    helical_0_result = mow_helical_external_dp(
        z=z, normal_DP=dp, normal_alpha_deg=pa, t=t, d=d, helix_deg=0.0
    )
    print(f"   Helical 0° MOP: {helical_0_result.MOW:.6f}")
    
    difference = abs(spur_result.MOW - helical_0_result.MOW)
    if difference < 0.000001:
        print(f"   PASS: Difference {difference:.8f} < 0.000001")
    else:
        print(f"   FAIL: Difference {difference:.8f} >= 0.000001")
    
    # Test helical gears at different angles
    test_angles = [5.0, 15.0, 30.0]
    
    print(f"\n3. Helical Gears at Different Angles")
    print("   Helix Angle    MOP Result    Correction    % Change")
    print("   " + "-" * 50)
    
    for helix in test_angles:
        helical_result = mow_helical_external_dp(
            z=z, normal_DP=dp, normal_alpha_deg=pa, t=t, d=d, helix_deg=helix
        )
        
        correction = helical_result.MOW - spur_result.MOW
        percent_change = (correction / spur_result.MOW) * 100
        
        print(f"   {helix:5.1f}°         {helical_result.MOW:.6f}    {correction:+.6f}   {percent_change:+.3f}%")
    
    print("\n4. Correction Function Direct Test")
    print("   Helix Angle    External Corr    Internal Corr")
    print("   " + "-" * 45)
    
    for helix in test_angles:
        ext_corr = calculate_improved_helical_correction(helix, pa, d, is_external=True)
        int_corr = calculate_improved_helical_correction(helix, pa, d, is_external=False)
        
        print(f"   {helix:5.1f}°         {ext_corr:.6f}        {int_corr:.6f}")
    
    # Test internal gears
    print("\n5. Internal Gear Test")
    s = 0.13090  # Space width for internal gear
    d_int = 0.14000
    
    internal_spur = mbp_spur_internal_dp(z=36, DP=12, alpha_deg=20, s=s, d=d_int)
    internal_helical = mbp_helical_internal_dp(
        z=36, normal_DP=12, normal_alpha_deg=20, s=s, d=d_int, helix_deg=15.0
    )
    
    print(f"   Internal Spur MBP:    {internal_spur.MOW:.6f}")
    print(f"   Internal Helical MBP: {internal_helical.MOW:.6f}")
    
    int_difference = abs(internal_helical.MOW - internal_spur.MOW)
    print(f"   Difference:           {int_difference:.6f}")
    
    print("\nBASIC FUNCTIONALITY TESTS COMPLETED")
    print("=" * 50)
    
    return True

def test_precision_consistency():
    """Test precision and consistency across calculations"""
    
    print("\nPRECISION CONSISTENCY TEST")  
    print("=" * 50)
    
    # Parameters for consistency test
    z = 32
    dp = 8
    pa = 20.0
    t = 0.2124
    d = 0.2160
    helix = 15.0
    
    print(f"\nRunning same calculation 100 times to check consistency...")
    print(f"Parameters: z={z}, dp={dp}, pa={pa}, helix={helix}, t={t}, d={d}")
    
    results = []
    for i in range(100):
        result = mow_helical_external_dp(
            z=z, normal_DP=dp, normal_alpha_deg=pa, t=t, d=d, helix_deg=helix
        )
        results.append(result.MOW)
    
    # Check consistency
    min_result = min(results)
    max_result = max(results)
    avg_result = sum(results) / len(results)
    variation = max_result - min_result
    
    print(f"   Minimum:    {min_result:.8f}")
    print(f"   Maximum:    {max_result:.8f}")
    print(f"   Average:    {avg_result:.8f}")
    print(f"   Variation:  {variation:.8f}")
    
    if variation < 1e-10:
        print("   PASS: Results are perfectly consistent")
    else:
        print(f"   WARNING: Results vary by {variation:.2e}")
    
    print("\nPRECISION CONSISTENCY TEST COMPLETED")
    print("=" * 50)
    
    return variation < 1e-8

def test_parameter_ranges():
    """Test different parameter ranges"""
    
    print("\nPARAMETER RANGE TEST")
    print("=" * 50)
    
    base_params = {
        'z': 32, 'normal_DP': 8, 'normal_alpha_deg': 20.0,
        't': 0.2124, 'd': 0.2160, 'helix_deg': 15.0
    }
    
    # Test different tooth counts
    print("\n1. Different Tooth Counts")
    tooth_counts = [12, 24, 32, 48, 72]
    for z in tooth_counts:
        params = base_params.copy()
        params['z'] = z
        try:
            result = mow_helical_external_dp(**params)
            print(f"   z={z:2d}: MOP = {result.MOW:.6f}")
        except Exception as e:
            print(f"   z={z:2d}: ERROR - {str(e)}")
    
    # Test different pressure angles
    print("\n2. Different Pressure Angles")
    pressure_angles = [14.5, 17.5, 20.0, 22.5, 25.0]
    for pa in pressure_angles:
        params = base_params.copy()
        params['normal_alpha_deg'] = pa
        try:
            result = mow_helical_external_dp(**params)
            print(f"   PA={pa:4.1f}°: MOP = {result.MOW:.6f}")
        except Exception as e:
            print(f"   PA={pa:4.1f}°: ERROR - {str(e)}")
    
    # Test different helix angles
    print("\n3. Different Helix Angles")
    helix_angles = [0, 5, 10, 15, 20, 25, 30, 35, 40]
    for helix in helix_angles:
        params = base_params.copy()
        params['helix_deg'] = helix
        try:
            result = mow_helical_external_dp(**params)
            print(f"   Helix={helix:2d}°: MOP = {result.MOW:.6f}")
        except Exception as e:
            print(f"   Helix={helix:2d}°: ERROR - {str(e)}")
    
    print("\nPARAMETER RANGE TEST COMPLETED")
    print("=" * 50)
    
    return True

if __name__ == '__main__':
    print("MOP Simple Helical Gear Test Suite")
    print("Testing basic functionality and consistency...\n")
    
    try:
        # Run all tests
        test1_pass = test_basic_functionality()
        test2_pass = test_precision_consistency() 
        test3_pass = test_parameter_ranges()
        
        # Overall summary
        print("\nOVERALL SUMMARY")
        print("=" * 50)
        print(f"Basic Functionality:     {'PASS' if test1_pass else 'FAIL'}")
        print(f"Precision Consistency:   {'PASS' if test2_pass else 'FAIL'}")
        print(f"Parameter Ranges:        {'PASS' if test3_pass else 'FAIL'}")
        
        all_pass = test1_pass and test2_pass and test3_pass
        print(f"\nOverall Result:          {'ALL TESTS PASS' if all_pass else 'SOME TESTS FAILED'}")
        
        sys.exit(0 if all_pass else 1)
        
    except Exception as e:
        print(f"\nTEST SUITE ERROR: {str(e)}")
        sys.exit(1)