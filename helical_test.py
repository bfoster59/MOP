#!/usr/bin/env python3
"""
Test script to investigate helical gear MOP calculation discrepancy.
Analyzes the specific case: z=127, DP=12, PA=20°, helix=10.5°, t=0.130900, d=0.144
"""

import math
from MOP import mow_helical_external_dp, helical_conversions, PI_HIGH_PRECISION

def analyze_helical_discrepancy():
    """Analyze the helical gear MOP discrepancy."""
    
    # Test parameters
    z = 127
    normal_dp = 12.0
    normal_pa_deg = 20.0
    helix_deg = 10.5
    t = 0.130900
    d = 0.144
    
    print("=== Helical Gear MOP Analysis ===")
    print(f"Parameters: z={z}, normal_DP={normal_dp}, normal_PA={normal_pa_deg}°")
    print(f"           helix={helix_deg}°, t={t:.6f}, d={d:.6f}")
    print()
    
    # Calculate using current method
    result = mow_helical_external_dp(z, normal_dp, normal_pa_deg, t, d, helix_deg)
    current_mop = result.MOW
    
    print(f"Current calculation: {current_mop:.6f} inches")
    print(f"AGMA reference:      10.967749 inches")
    print(f"Discrepancy:        {10.967749 - current_mop:.6f} inches")
    print()
    
    # Analyze the conversion process
    trans_pa_deg, trans_dp, base_helix_deg, lead_coeff = helical_conversions(normal_pa_deg, helix_deg, normal_dp)
    
    print("=== Parameter Conversions ===")
    print(f"Normal PA:     {normal_pa_deg:.6f}°")
    print(f"Transverse PA: {trans_pa_deg:.6f}°")
    print(f"Normal DP:     {normal_dp:.6f}")
    print(f"Transverse DP: {trans_dp:.6f}")
    print(f"Base helix:    {base_helix_deg:.6f}°")
    print()
    
    # Calculate transverse tooth thickness
    helix_rad = helix_deg * (PI_HIGH_PRECISION / 180.0)
    trans_tooth_thickness = t / math.cos(helix_rad)
    
    print(f"Normal thickness:     {t:.6f}")
    print(f"Transverse thickness: {trans_tooth_thickness:.6f}")
    print(f"cos(helix):          {math.cos(helix_rad):.6f}")
    print()
    
    # Investigate potential correction factors
    investigate_corrections(z, normal_dp, normal_pa_deg, helix_deg, t, d, current_mop)

def investigate_corrections(z, normal_dp, normal_pa_deg, helix_deg, t, d, current_mop):
    """Investigate potential correction factors."""
    
    target_mop = 10.967749
    discrepancy = target_mop - current_mop
    
    print("=== Investigation of Potential Corrections ===")
    
    # 1. Base helix angle correction
    helix_rad = helix_deg * (PI_HIGH_PRECISION / 180.0)
    normal_pa_rad = normal_pa_deg * (PI_HIGH_PRECISION / 180.0)
    
    # Calculate base helix angle
    trans_pa_rad = math.atan(math.tan(normal_pa_rad) / math.cos(helix_rad))
    base_helix_rad = math.atan(math.tan(helix_rad) * math.cos(trans_pa_rad))
    base_helix_deg = base_helix_rad * (180.0 / PI_HIGH_PRECISION)
    
    print(f"Base helix angle: {base_helix_deg:.6f}°")
    
    # 2. Axial component analysis
    # The discrepancy might be related to axial positioning effects
    pitch_diameter = z / (normal_dp * math.cos(helix_rad))
    base_diameter = pitch_diameter * math.cos(trans_pa_rad)
    
    print(f"Pitch diameter:   {pitch_diameter:.6f}")
    print(f"Base diameter:    {base_diameter:.6f}")
    
    # 3. Test different correction approaches
    print(f"\nDiscrepancy analysis:")
    print(f"Target - Current = {discrepancy:.6f}")
    print(f"Relative error = {(discrepancy/target_mop)*100:.4f}%")
    
    # 4. Potential axial correction
    # For helical gears, there might be an axial component to the measurement
    axial_correction = discrepancy
    print(f"\nPotential axial correction: {axial_correction:.6f}")
    
    # 5. Check if it's related to helix angle
    helix_factor = math.cos(helix_rad)
    potential_helix_correction = discrepancy / helix_factor
    print(f"Helix-related factor: {potential_helix_correction:.6f}")
    
    # 6. Test base helix angle effects
    base_helix_correction = discrepancy / math.cos(base_helix_rad)
    print(f"Base helix correction: {base_helix_correction:.6f}")
    
    # 7. Lead angle effects
    lead_angle_rad = math.atan(1.0 / math.tan(helix_rad))
    lead_correction = discrepancy / math.cos(lead_angle_rad)
    print(f"Lead angle correction: {lead_correction:.6f}")

def test_alternative_formulations():
    """Test alternative helical gear MOP formulations."""
    
    print("\n=== Testing Alternative Formulations ===")
    
    # Parameters
    z = 127
    normal_dp = 12.0
    normal_pa_deg = 20.0
    helix_deg = 10.5
    t = 0.130900
    d = 0.144
    
    helix_rad = helix_deg * (PI_HIGH_PRECISION / 180.0)
    normal_pa_rad = normal_pa_deg * (PI_HIGH_PRECISION / 180.0)
    
    # Method 1: Direct normal plane calculation (not converting to transverse)
    # This might be more appropriate for helical gears
    normal_dp_val = normal_dp
    normal_pa_val = normal_pa_deg
    
    # Calculate pitch diameter in normal plane
    pitch_dia_normal = z / normal_dp_val
    base_dia_normal = pitch_dia_normal * math.cos(normal_pa_rad)
    
    print(f"Normal plane approach:")
    print(f"Pitch dia (normal): {pitch_dia_normal:.6f}")
    print(f"Base dia (normal):  {base_dia_normal:.6f}")
    
    # Method 2: Apply helix correction to the final result
    current_result = mow_helical_external_dp(z, normal_dp, normal_pa_deg, t, d, helix_deg)
    
    # Potential corrections to test
    corrections = {
        "None": 0.0,
        "cos(helix)": (1.0 - math.cos(helix_rad)) * current_result.MOW,
        "sin(helix)": math.sin(helix_rad) * (d / 2.0),
        "Base helix factor": math.sin(math.atan(math.tan(helix_rad) * math.cos(normal_pa_rad))) * (d),
        "Axial positioning": 0.006819,  # The exact discrepancy
        "Lead angle component": math.tan(helix_rad) * (t / 2.0),
    }
    
    print(f"\nTesting corrections:")
    print(f"Current MOP: {current_result.MOW:.6f}")
    
    for name, correction in corrections.items():
        corrected_mop = current_result.MOW + correction
        error = abs(10.967749 - corrected_mop)
        print(f"{name:20s}: {corrected_mop:.6f} (error: {error:.6f})")

if __name__ == "__main__":
    analyze_helical_discrepancy()
    test_alternative_formulations()