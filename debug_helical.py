#!/usr/bin/env python3
"""
Debug helical gear calculations to match reference calculators
Analyzing the 0.002691" difference at 5° helix angle
"""

import math
from MOP import (
    mow_spur_external_dp, mow_helical_external_dp,
    helical_conversions, calculate_improved_helical_correction,
    PI_HIGH_PRECISION
)

def debug_helical_calculation():
    """Debug the helical calculation step by step"""
    
    # Parameters from the screenshot comparison
    z = 127
    normal_dp = 12  # Normal DP
    normal_pa = 20  # Normal pressure angle
    helix = 5.0     # Helix angle
    t = 0.13090     # Normal tooth thickness
    d = 0.144       # Pin diameter
    
    print("=" * 60)
    print("HELICAL GEAR DEBUG - 5° Helix Angle")
    print("=" * 60)
    print(f"Input Parameters:")
    print(f"  Teeth (z): {z}")
    print(f"  Normal DP: {normal_dp}")
    print(f"  Normal PA: {normal_pa}°")
    print(f"  Helix: {helix}°")
    print(f"  Normal tooth thickness: {t}")
    print(f"  Pin diameter: {d}")
    print()
    
    # Step 1: Convert to transverse parameters
    trans_pa, trans_dp, base_helix, lead_coeff = helical_conversions(normal_pa, helix, normal_dp)
    
    print("Step 1: Parameter Conversions")
    print(f"  Normal DP -> Transverse DP: {normal_dp} -> {trans_dp:.6f}")
    print(f"  Normal PA -> Transverse PA: {normal_pa} -> {trans_pa:.6f}")
    print(f"  Base helix angle: {base_helix:.6f}°")
    print()
    
    # Step 2: Convert tooth thickness
    helix_rad = helix * (PI_HIGH_PRECISION / 180.0)
    trans_thickness = t / math.cos(helix_rad)
    
    print("Step 2: Tooth Thickness Conversion")
    print(f"  Normal thickness -> Transverse: {t} -> {trans_thickness:.6f}")
    print(f"  Conversion factor (1/cos({helix}°)): {1/math.cos(helix_rad):.6f}")
    print()
    
    # Step 3: Spur gear calculation with transverse parameters
    spur_result = mow_spur_external_dp(z, trans_dp, trans_pa, trans_thickness, d)
    
    print("Step 3: Spur Calculation with Transverse Parameters")
    print(f"  Spur MOP result: {spur_result.MOW:.6f}")
    print(f"  Method: {spur_result.method}")
    print()
    
    # Step 4: Apply helical correction
    helical_correction = calculate_improved_helical_correction(helix, normal_pa, d, is_external=True)
    corrected_mop = spur_result.MOW + helical_correction
    
    print("Step 4: Helical Correction")
    print(f"  Helical correction: {helical_correction:.6f}")
    print(f"  Final MOP: {spur_result.MOW:.6f} + {helical_correction:.6f} = {corrected_mop:.6f}")
    print()
    
    # Step 5: Compare with our helical function
    helical_result = mow_helical_external_dp(z, normal_dp, normal_pa, t, d, helix)
    
    print("Step 5: Our Helical Function Result")
    print(f"  Our result: {helical_result.MOW:.6f}")
    print(f"  Match check: {'PASS' if abs(helical_result.MOW - corrected_mop) < 1e-6 else 'FAIL'}")
    print()
    
    # Step 6: Analyze the issue
    print("Step 6: Analysis vs Reference")
    reference_value = 10.827894  # From ZakGear/GearCutter
    our_value = helical_result.MOW
    difference = our_value - reference_value
    
    print(f"  Reference value: {reference_value}")
    print(f"  Our value: {our_value:.6f}")
    print(f"  Difference: {difference:+.6f}")
    print(f"  Error percentage: {abs(difference/reference_value)*100:.4f}%")
    print()
    
    # Test alternative calculation approach
    print("Step 7: Alternative Approach Test")
    
    # Try without the additional helical correction
    no_correction_result = spur_result.MOW
    diff_no_correction = no_correction_result - reference_value
    
    print(f"  Without helical correction: {no_correction_result:.6f}")
    print(f"  Difference from reference: {diff_no_correction:+.6f}")
    print()
    
    # Try with different tooth thickness handling
    # Maybe we should use normal thickness directly?
    spur_result_normal_t = mow_spur_external_dp(z, trans_dp, trans_pa, t, d)  # Use normal thickness
    diff_normal_t = spur_result_normal_t.MOW - reference_value
    
    print(f"  With normal thickness (not converted): {spur_result_normal_t.MOW:.6f}")
    print(f"  Difference from reference: {diff_normal_t:+.6f}")
    print()
    
    return {
        'reference': reference_value,
        'our_result': our_value,
        'difference': difference,
        'spur_with_trans_params': no_correction_result,
        'spur_with_normal_thickness': spur_result_normal_t.MOW
    }

def test_different_approaches():
    """Test different calculation approaches"""
    
    print("=" * 60)
    print("TESTING DIFFERENT HELICAL APPROACHES")
    print("=" * 60)
    
    # Same parameters
    z = 127
    normal_dp = 12
    normal_pa = 20
    helix = 5.0
    t = 0.13090
    d = 0.144
    reference = 10.827894
    
    approaches = []
    
    # Approach 1: Current method
    result1 = mow_helical_external_dp(z, normal_dp, normal_pa, t, d, helix)
    approaches.append(("Current method", result1.MOW))
    
    # Approach 2: No helical correction, just parameter conversion
    trans_pa, trans_dp, _, _ = helical_conversions(normal_pa, helix, normal_dp)
    helix_rad = helix * (PI_HIGH_PRECISION / 180.0)
    trans_thickness = t / math.cos(helix_rad)
    result2 = mow_spur_external_dp(z, trans_dp, trans_pa, trans_thickness, d)
    approaches.append(("Transverse params + converted thickness", result2.MOW))
    
    # Approach 3: Transverse params but normal thickness
    result3 = mow_spur_external_dp(z, trans_dp, trans_pa, t, d)
    approaches.append(("Transverse params + normal thickness", result3.MOW))
    
    # Approach 4: Normal params with spur calculation (baseline)
    result4 = mow_spur_external_dp(z, normal_dp, normal_pa, t, d)
    approaches.append(("Normal params (spur baseline)", result4.MOW))
    
    print("Approach Testing Results:")
    print("-" * 60)
    for name, value in approaches:
        difference = value - reference
        error_pct = abs(difference / reference) * 100
        print(f"{name:<40}: {value:.6f} ({difference:+.6f}, {error_pct:.4f}%)")
    
    print(f"\nReference value: {reference}")
    
    # Find closest approach
    closest = min(approaches, key=lambda x: abs(x[1] - reference))
    print(f"Closest approach: {closest[0]} with error {abs(closest[1] - reference):.6f}")

if __name__ == '__main__':
    debug_results = debug_helical_calculation()
    print()
    test_different_approaches()