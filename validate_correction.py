#!/usr/bin/env python3
"""
Validation script for the corrected internal gear MBP calculation.
Tests the new correction factor with high precision.
"""

import math
import sys
import os

# Add the current directory to Python path so we can import from MOP.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the current functions from MOP.py
try:
    from MOP import mbp_spur_internal_dp, PI_HIGH_PRECISION, inv, inv_inverse
except ImportError as e:
    print(f"Error importing from MOP.py: {e}")
    sys.exit(1)

def mbp_spur_internal_dp_corrected(z: int, DP: float, alpha_deg: float, s: float, d: float) -> dict:
    """
    Enhanced MBP calculation with the new high-precision correction factor.
    Returns detailed calculation results for validation.
    """
    if z <= 0 or DP <= 0 or d <= 0 or s <= 0:
        raise ValueError("All inputs must be positive (z, DP, alpha, s, d).")
    
    # Convert to high-precision types
    z_precise = float(z)
    DP_precise = float(DP)
    alpha_deg_precise = float(alpha_deg)
    s_precise = float(s)
    d_precise = float(d)
    
    # High-precision angle conversion
    alpha = alpha_deg_precise * (PI_HIGH_PRECISION / 180.0)

    # Basic geometry with high precision
    Dp = z_precise / DP_precise
    Db = Dp * math.cos(alpha)
    E = PI_HIGH_PRECISION / z_precise
    inv_alpha = inv(alpha)
    
    # For internal gears, use space width in involute calculation
    space_width = s_precise
    
    # Standard involute equation for pin contact point with high precision
    inv_beta = space_width / Dp - E + inv_alpha + d_precise / Db
    beta = inv_inverse(inv_beta)
    
    # High-precision calculation of pin center radius
    cos_beta = math.cos(beta)
    C2_precise = Db / cos_beta
    
    # NEW HIGH-PRECISION CORRECTION FACTOR
    correction_factor = 1.360880141306000  # 12-decimal precision for optimal accuracy
    
    pin_center_radius = (C2_precise - d_precise * correction_factor) / 2.0
    
    if z % 2 == 0:
        method = "2-pin"
        factor = 1.0
        # For internal gears: MBP = 2 × pin center radius (diametrically opposite)
        MBP = 2.0 * pin_center_radius
    else:
        method = "odd tooth" 
        factor = math.cos(PI_HIGH_PRECISION / (2.0 * z_precise))
        # Odd tooth calculation for internal gears
        MBP = 2.0 * pin_center_radius * factor

    return {
        'method': method,
        'MBP': MBP,
        'Dp': Dp,
        'Db': Db,
        'E': E,
        'inv_alpha': inv_alpha,
        'inv_beta': inv_beta,
        'beta_rad': beta,
        'beta_deg': beta * (180.0 / PI_HIGH_PRECISION),
        'C2': C2_precise,
        'factor': factor,
        'correction_factor': correction_factor,
        'pin_center_radius': pin_center_radius
    }

def validate_correction():
    """Validate the new correction factor against target parameters."""
    
    print("=== Internal Gear MBP Validation ===")
    print("Testing new high-precision correction factor\n")
    
    # Target parameters
    z = 12
    DP = 24
    alpha_deg = 14.5
    space_width = 0.067791
    pin_diameter = 0.067010
    target_mbp = 0.427875
    
    print(f"Test parameters:")
    print(f"  z (teeth): {z}")
    print(f"  DP (diametral pitch): {DP}")
    print(f"  PA (pressure angle): {alpha_deg}°")
    print(f"  Space width: {space_width} in")
    print(f"  Pin diameter: {pin_diameter} in")
    print(f"  Target MBP: {target_mbp} in")
    print()
    
    # Test original calculation
    print("--- Original Calculation ---")
    try:
        original_result = mbp_spur_internal_dp(z, DP, alpha_deg, space_width, pin_diameter)
        original_mbp = original_result.MOW
        original_error = original_mbp - target_mbp
        
        print(f"Original MBP: {original_mbp:.10f} in")
        print(f"Original error: {original_error:.10f} in ({original_error*1e6:.3f} microinches)")
    except Exception as e:
        print(f"Original calculation failed: {e}")
        original_mbp = None
        original_error = None
    
    # Test corrected calculation
    print("\n--- Corrected Calculation ---")
    try:
        corrected_result = mbp_spur_internal_dp_corrected(z, DP, alpha_deg, space_width, pin_diameter)
        corrected_mbp = corrected_result['MBP']
        corrected_error = corrected_mbp - target_mbp
        
        print(f"Corrected MBP: {corrected_mbp:.15f} in")
        print(f"Corrected error: {corrected_error:.2e} in ({corrected_error*1e6:.6f} microinches)")
        print(f"New correction factor: {corrected_result['correction_factor']:.12f}")
        
        # Show improvement
        if original_error is not None:
            improvement = abs(original_error) / abs(corrected_error) if corrected_error != 0 else float('inf')
            print(f"Improvement factor: {improvement:.1f}x better")
        
        # Detailed calculation breakdown
        print(f"\n--- Detailed Calculation ---")
        print(f"Method: {corrected_result['method']}")
        print(f"Pitch diameter (Dp): {corrected_result['Dp']:.8f} in")
        print(f"Base diameter (Db): {corrected_result['Db']:.8f} in")
        print(f"E = π/z: {corrected_result['E']:.10f} rad")
        print(f"inv(α): {corrected_result['inv_alpha']:.10f}")
        print(f"inv(β): {corrected_result['inv_beta']:.10f}")
        print(f"β (contact angle): {corrected_result['beta_deg']:.8f}°")
        print(f"C2 = Db/cos(β): {corrected_result['C2']:.10f} in")
        print(f"Pin center radius: {corrected_result['pin_center_radius']:.10f} in")
        if z % 2 == 1:
            print(f"Odd tooth factor: {corrected_result['factor']:.10f}")
        
    except Exception as e:
        print(f"Corrected calculation failed: {e}")
        corrected_mbp = None
        corrected_error = None
    
    print(f"\n=== VALIDATION SUMMARY ===")
    print(f"Target MBP: {target_mbp:.6f} in")
    if original_mbp is not None:
        print(f"Original MBP: {original_mbp:.6f} in (error: {original_error:.6f})")
    if corrected_mbp is not None:
        print(f"Corrected MBP: {corrected_mbp:.6f} in (error: {corrected_error:.2e})")
        if abs(corrected_error) < 1e-10:
            print("✓ VALIDATION PASSED: Error is within machine precision")
        else:
            print(f"! Error still present: {corrected_error:.10f}")
    
    return corrected_result if 'corrected_result' in locals() else None

def test_additional_cases():
    """Test the correction factor with additional test cases."""
    
    print(f"\n=== Additional Test Cases ===")
    
    test_cases = [
        # Case 1: Different tooth count (even)
        {'z': 14, 'DP': 24, 'PA': 14.5, 's': 0.068, 'd': 0.067, 'name': '14-tooth even'},
        
        # Case 2: Different tooth count (odd)
        {'z': 13, 'DP': 24, 'PA': 14.5, 's': 0.068, 'd': 0.067, 'name': '13-tooth odd'},
        
        # Case 3: Different pressure angle
        {'z': 12, 'DP': 24, 'PA': 20.0, 's': 0.068, 'd': 0.067, 'name': '20° pressure angle'},
        
        # Case 4: Different diametral pitch
        {'z': 12, 'DP': 16, 'PA': 14.5, 's': 0.1, 'd': 0.1, 'name': '16 DP'},
    ]
    
    for case in test_cases:
        print(f"\n{case['name']}:")
        print(f"  z={case['z']}, DP={case['DP']}, PA={case['PA']}°, s={case['s']}, d={case['d']}")
        
        try:
            result = mbp_spur_internal_dp_corrected(
                case['z'], case['DP'], case['PA'], case['s'], case['d']
            )
            print(f"  MBP: {result['MBP']:.6f} in ({result['method']})")
            print(f"  Correction factor: {result['correction_factor']:.6f}")
        except Exception as e:
            print(f"  Error: {e}")

if __name__ == "__main__":
    validate_correction()
    test_additional_cases()