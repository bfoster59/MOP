#!/usr/bin/env python3
"""
Test the corrected helical gear MOP calculation.
"""

from MOP import mow_helical_external_dp

def test_corrected_calculation():
    """Test the corrected helical gear calculation."""
    
    # Test parameters - the original case
    z = 127
    normal_dp = 12.0
    normal_pa_deg = 20.0
    helix_deg = 10.5
    t = 0.130900
    d = 0.144
    
    print("=== Testing Corrected Helical Gear MOP Calculation ===")
    print(f"Parameters: z={z}, normal_DP={normal_dp}, normal_PA={normal_pa_deg}°")
    print(f"           helix={helix_deg}°, t={t:.6f}, d={d:.6f}")
    print()
    
    # Calculate with corrected function
    result = mow_helical_external_dp(z, normal_dp, normal_pa_deg, t, d, helix_deg)
    
    print(f"Corrected calculation: {result.MOW:.6f} inches")
    print(f"AGMA reference:        10.967749 inches")
    print(f"Error:                 {abs(10.967749 - result.MOW):.6f} inches")
    print()
    
    # Test with additional cases to verify the correction works generally
    test_cases = [
        # z, normal_dp, normal_pa_deg, helix_deg, t, d, description
        (45, 8, 20, 15.0, 0.196, 0.21, "Different helix angle"),
        (60, 10, 25, 10.5, 0.157, 0.17, "Different pressure angle"),
        (32, 6, 20, 10.5, 0.262, 0.28, "Different tooth count"),
        (127, 12, 20, 0.0, 0.130900, 0.144, "Spur gear (helix=0)"),
    ]
    
    print("=== Testing Additional Cases ===")
    
    for z_test, dp_test, pa_test, helix_test, t_test, d_test, desc in test_cases:
        result_test = mow_helical_external_dp(z_test, dp_test, pa_test, t_test, d_test, helix_test)
        
        print(f"{desc}:")
        print(f"  Parameters: z={z_test}, DP={dp_test}, PA={pa_test}°, helix={helix_test}°")
        print(f"  MOP: {result_test.MOW:.6f} inches")
        
        if helix_test > 0.01:
            # Calculate what the correction was
            import math
            from MOP import PI_HIGH_PRECISION
            helix_rad = helix_test * (PI_HIGH_PRECISION / 180.0)
            pa_rad = pa_test * (PI_HIGH_PRECISION / 180.0)
            correction = 0.76 * d_test * math.sin(helix_rad) * math.sin(pa_rad)
            print(f"  Helical correction applied: {correction:.6f} inches")
        else:
            print(f"  No helical correction (spur gear)")
        
        print()

if __name__ == "__main__":
    test_corrected_calculation()