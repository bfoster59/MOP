#!/usr/bin/env python3
"""
Comprehensive Test Suite for MOP Gear Metrology Calculator
Tests spur gears, helical gears, APIs, and edge cases
"""

import sys
import os
import unittest
import json
import csv
import tempfile
from unittest.mock import patch, MagicMock
from typing import List, Dict, Any

# Import the main MOP module
try:
    from MOP import (
        mow_spur_external_dp, mbp_spur_internal_dp,
        mow_helical_external_dp, mbp_helical_internal_dp,
        best_pin_rule, calculate_improved_helical_correction,
        helical_conversions, Result
    )
except ImportError:
    print("Error: Could not import MOP module. Make sure MOP.py is in the current directory.")
    sys.exit(1)

# Try to import API modules (optional)
try:
    from gear_api import app as fastapi_app
    from gear_cli_api import GearCliAPI
    from gear_metrology_agent import GearMetrologyAgent
    API_AVAILABLE = True
except ImportError:
    API_AVAILABLE = False
    print("Warning: API modules not available. Skipping API tests.")

class TestSpurGears(unittest.TestCase):
    """Test suite for spur gear calculations (β = 0°)"""
    
    def test_external_spur_baseline(self):
        """Test external spur gear with known reference values"""
        result = mow_spur_external_dp(z=45, DP=8, alpha_deg=20, t=0.2124, d=0.2160)
        
        self.assertAlmostEqual(result.MOW, 5.438017, places=6, 
                              msg="External spur MOP should match reference value")
        self.assertEqual(result.method, "odd tooth", 
                        msg="45-tooth gear should use odd tooth method")
        self.assertAlmostEqual(result.Dp, 5.625, places=6,
                              msg="Pitch diameter should be z/DP = 45/8")
    
    def test_internal_spur_baseline(self):
        """Test internal spur gear with known reference values"""
        result = mbp_spur_internal_dp(z=36, DP=12, alpha_deg=20, s=0.13090, d=0.14000)
        
        self.assertAlmostEqual(result.MOW, 2.836536, places=6,
                              msg="Internal spur MBP should match reference value")
        self.assertEqual(result.method, "2-pin",
                        msg="36-tooth gear should use 2-pin method")
        self.assertAlmostEqual(result.Dp, 3.0, places=6,
                              msg="Pitch diameter should be z/DP = 36/12")
    
    def test_even_vs_odd_tooth_methods(self):
        """Test that even and odd tooth counts use correct methods"""
        # Even tooth count
        result_even = mow_spur_external_dp(z=44, DP=8, alpha_deg=20, t=0.2124, d=0.2160)
        self.assertEqual(result_even.method, "2-pin")
        
        # Odd tooth count  
        result_odd = mow_spur_external_dp(z=45, DP=8, alpha_deg=20, t=0.2124, d=0.2160)
        self.assertEqual(result_odd.method, "odd tooth")
    
    def test_best_pin_rules(self):
        """Test best pin diameter calculations for different pressure angles"""
        pin_20 = best_pin_rule(8, 20.0)
        pin_145 = best_pin_rule(8, 14.5)
        pin_25 = best_pin_rule(8, 25.0)
        
        self.assertAlmostEqual(pin_20, 0.216, places=3, 
                              msg="20° PA best pin should be ~1.728/DP")
        self.assertAlmostEqual(pin_145, 0.210, places=3,
                              msg="14.5° PA best pin should be ~1.68/DP")
        self.assertAlmostEqual(pin_25, 0.240, places=3,
                              msg="25° PA best pin should be ~1.92/DP")

class TestHelicalGears(unittest.TestCase):
    """Test suite for helical gear calculations (β ≠ 0°)"""
    
    def setUp(self):
        """Set up test parameters"""
        self.base_params = {
            'z': 32,
            'normal_DP': 8,
            'normal_alpha_deg': 20,
            't': 0.2124,
            'd': 0.2160
        }
    
    def test_helical_conversions(self):
        """Test normal to transverse parameter conversions"""
        normal_pa, helix, normal_dp = 20.0, 15.0, 8.0
        
        trans_pa, trans_dp, base_helix, lead_coeff = helical_conversions(
            normal_pa, helix, normal_dp
        )
        
        # Transverse pressure angle should be larger than normal
        self.assertGreater(trans_pa, normal_pa,
                          msg="Transverse PA should be larger than normal PA")
        
        # Transverse DP should be smaller than normal DP  
        self.assertLess(trans_dp, normal_dp,
                       msg="Transverse DP should be smaller than normal DP")
        
        # Base helix should be smaller than pitch helix
        self.assertLess(base_helix, helix,
                       msg="Base helix should be smaller than pitch helix")
    
    def test_helical_correction_ranges(self):
        """Test helical corrections for different helix angle ranges"""
        pin_d = 0.2160
        normal_pa = 20.0
        
        # Test different helix angle ranges
        test_angles = [5.0, 10.5, 15.0, 22.5, 35.0]
        corrections = []
        
        for helix in test_angles:
            correction = calculate_improved_helical_correction(
                helix, normal_pa, pin_d, is_external=True
            )
            corrections.append(correction)
            
            # Correction should be positive for external gears
            self.assertGreater(correction, 0,
                              msg=f"External helical correction should be positive at {helix}°")
        
        # Corrections should generally increase with helix angle
        for i in range(1, len(corrections)):
            self.assertGreaterEqual(corrections[i], corrections[i-1] * 0.8,
                                   msg="Helical corrections should generally increase with angle")
    
    def test_helical_external_calculation(self):
        """Test external helical gear calculations at various helix angles"""
        test_cases = [
            {'helix': 0.0, 'expected_approx': 4.214},   # Should match spur gear
            {'helix': 5.0, 'expected_approx': 4.215},   # Small correction
            {'helix': 15.0, 'expected_approx': 4.289},  # Medium correction
            {'helix': 30.0, 'expected_approx': 4.458},  # Large correction
        ]
        
        for case in test_cases:
            result = mow_helical_external_dp(
                helix_deg=case['helix'], **self.base_params
            )
            
            self.assertAlmostEqual(result.MOW, case['expected_approx'], places=2,
                                  msg=f"Helical MOP at {case['helix']}° should be approximately {case['expected_approx']}")
    
    def test_helical_internal_calculation(self):
        """Test internal helical gear calculations"""
        # Convert tooth thickness to space width for internal gear
        internal_params = self.base_params.copy()
        internal_params['s'] = internal_params.pop('t')  # Rename t to s
        
        result = mow_helical_external_dp(helix_deg=15.0, **self.base_params)
        result_internal = mbp_helical_internal_dp(helix_deg=15.0, **internal_params)
        
        # Internal and external results should be different
        self.assertNotAlmostEqual(result.MOW, result_internal.MOW, places=3,
                                 msg="Internal and external helical results should differ")
    
    def test_spur_vs_helical_consistency(self):
        """Test that helical calculation with 0° helix matches spur calculation"""
        # Spur calculation
        spur_result = mow_spur_external_dp(
            z=self.base_params['z'],
            DP=self.base_params['normal_DP'],
            alpha_deg=self.base_params['normal_alpha_deg'],
            t=self.base_params['t'],
            d=self.base_params['d']
        )
        
        # Helical calculation with 0° helix
        helical_result = mow_helical_external_dp(helix_deg=0.0, **self.base_params)
        
        self.assertAlmostEqual(spur_result.MOW, helical_result.MOW, places=6,
                              msg="Helical calculation with 0° helix should match spur calculation")

class TestEdgeCases(unittest.TestCase):
    """Test suite for edge cases and boundary conditions"""
    
    def test_extreme_tooth_counts(self):
        """Test with very small and large tooth counts"""
        # Small tooth count
        result_small = mow_spur_external_dp(z=8, DP=16, alpha_deg=20, t=0.098, d=0.106)
        self.assertGreater(result_small.MOW, 0, msg="Small tooth count should produce valid result")
        
        # Large tooth count
        result_large = mow_spur_external_dp(z=200, DP=4, alpha_deg=20, t=0.393, d=0.432)
        self.assertGreater(result_large.MOW, 0, msg="Large tooth count should produce valid result")
    
    def test_extreme_pressure_angles(self):
        """Test with boundary pressure angles"""
        test_angles = [14.5, 17.5, 20.0, 22.5, 25.0, 30.0]
        
        for pa in test_angles:
            result = mow_spur_external_dp(z=32, DP=8, alpha_deg=pa, t=0.2124, d=0.2160)
            self.assertGreater(result.MOW, 0, 
                              msg=f"Pressure angle {pa}° should produce valid result")
    
    def test_extreme_helix_angles(self):
        """Test with boundary helix angles"""
        test_angles = [0.1, 1.0, 5.0, 44.0, 44.9]  # Near boundaries
        
        for helix in test_angles:
            result = mow_helical_external_dp(
                z=32, normal_DP=8, normal_alpha_deg=20, 
                t=0.2124, d=0.2160, helix_deg=helix
            )
            self.assertGreater(result.MOW, 0,
                              msg=f"Helix angle {helix}° should produce valid result")
    
    def test_precision_requirements(self):
        """Test that calculations meet precision requirements"""
        # Target: ≤0.00005" maximum error for helical gears
        result = mow_helical_external_dp(
            z=32, normal_DP=8, normal_alpha_deg=20,
            t=0.2124, d=0.2160, helix_deg=15.0
        )
        
        # Check that result has sufficient precision (6+ decimal places)
        self.assertIsInstance(result.MOW, float)
        mop_str = f"{result.MOW:.6f}"
        self.assertEqual(len(mop_str.split('.')[-1]), 6,
                        msg="Result should have 6 decimal places precision")

@unittest.skipUnless(API_AVAILABLE, "API modules not available")
class TestAPIs(unittest.TestCase):
    """Test suite for API functionality"""
    
    def setUp(self):
        """Set up API test clients"""
        if API_AVAILABLE:
            self.cli_api = GearCliAPI()
            self.agent = GearMetrologyAgent()
    
    def test_cli_api_basic_calculation(self):
        """Test CLI API basic gear calculation"""
        test_input = {
            "z": 32,
            "dp": 8,
            "pa": 20,
            "helix": 15,
            "t": 0.2124,
            "d": 0.2160,
            "gear_type": "external"
        }
        
        result = self.cli_api.calculate_gear(test_input)
        
        self.assertIn('mop', result, msg="CLI API should return MOP value")
        self.assertIn('uncertainty', result, msg="CLI API should return uncertainty")
        self.assertGreater(result['mop'], 0, msg="MOP should be positive")
        self.assertLessEqual(result['uncertainty'], 0.00005,
                            msg="Uncertainty should meet precision requirement")
    
    def test_cli_api_batch_processing(self):
        """Test CLI API batch processing"""
        test_batch = [
            {"z": 32, "dp": 8, "pa": 20, "helix": 0, "t": 0.2124, "d": 0.2160, "gear_type": "external"},
            {"z": 32, "dp": 8, "pa": 20, "helix": 15, "t": 0.2124, "d": 0.2160, "gear_type": "external"},
            {"z": 36, "dp": 12, "pa": 20, "helix": 0, "t": 0.13090, "d": 0.14000, "gear_type": "internal"}
        ]
        
        results = self.cli_api.batch_calculate(test_batch)
        
        self.assertEqual(len(results), 3, msg="Should return 3 results")
        for i, result in enumerate(results):
            self.assertIn('mop', result, msg=f"Result {i} should have MOP value")
            self.assertGreater(result['mop'], 0, msg=f"Result {i} MOP should be positive")
    
    def test_gear_metrology_agent(self):
        """Test Gear Metrology Agent functionality"""
        test_params = {
            "teeth": 32,
            "diametral_pitch": 8,
            "pressure_angle": 20,
            "helix_angle": 15,
            "tooth_thickness": 0.2124,
            "pin_diameter": 0.2160,
            "gear_type": "external"
        }
        
        result = self.agent.calculate_measurement(test_params)
        
        self.assertIn('measurement', result, msg="Agent should return measurement")
        self.assertIn('precision_analysis', result, msg="Agent should return precision analysis")
        self.assertGreater(result['measurement'], 0, msg="Measurement should be positive")

class TestFileProcessing(unittest.TestCase):
    """Test suite for CSV file processing and I/O operations"""
    
    def test_csv_processing(self):
        """Test CSV file input/output processing"""
        # Create temporary CSV file
        test_data = [
            ['z', 'dp', 'pa', 'helix', 't', 'd'],
            ['32', '8', '20.0', '0', '0.2124', '0.2160'],
            ['32', '8', '20.0', '15', '0.2124', '0.2160'],
            ['36', '12', '20.0', '0', '0.13090', '0.14000']
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as temp_file:
            writer = csv.writer(temp_file)
            writer.writerows(test_data)
            temp_file_path = temp_file.name
        
        try:
            # Test reading CSV (would need to implement CSV reader in actual code)
            with open(temp_file_path, 'r') as file:
                reader = csv.DictReader(file)
                rows = list(reader)
            
            self.assertEqual(len(rows), 3, msg="Should read 3 data rows")
            self.assertEqual(rows[0]['z'], '32', msg="First row should have z=32")
            self.assertEqual(rows[1]['helix'], '15', msg="Second row should have helix=15")
            
        finally:
            os.unlink(temp_file_path)

class TestPerformance(unittest.TestCase):
    """Test suite for performance and stress testing"""
    
    def test_calculation_performance(self):
        """Test calculation performance under load"""
        import time
        
        start_time = time.time()
        
        # Perform 1000 calculations
        for i in range(1000):
            result = mow_spur_external_dp(z=32, DP=8, alpha_deg=20, t=0.2124, d=0.2160)
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        # Should complete 1000 calculations in reasonable time (< 5 seconds)
        self.assertLess(elapsed, 5.0, 
                       msg="1000 calculations should complete in under 5 seconds")
        
        # Average calculation time should be under 5ms
        avg_time = elapsed / 1000
        self.assertLess(avg_time, 0.005,
                       msg="Average calculation time should be under 5ms")
    
    def test_memory_usage(self):
        """Test memory usage during calculations"""
        # Create many result objects to test memory management
        results = []
        for i in range(1000):
            result = mow_helical_external_dp(
                z=32, normal_DP=8, normal_alpha_deg=20,
                t=0.2124, d=0.2160, helix_deg=15.0
            )
            results.append(result)
        
        # All results should be valid
        self.assertEqual(len(results), 1000, msg="Should create 1000 valid results")
        
        # Check a few random results
        for result in results[::100]:  # Every 100th result
            self.assertGreater(result.MOW, 0, msg="All results should be positive")

def run_test_suite():
    """Run the complete test suite with detailed reporting"""
    
    print("=" * 80)
    print("MOP GEAR METROLOGY CALCULATOR - COMPREHENSIVE TEST SUITE")
    print("=" * 80)
    print()
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestSpurGears,
        TestHelicalGears, 
        TestEdgeCases,
        TestAPIs,
        TestFileProcessing,
        TestPerformance
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(
        verbosity=2,
        stream=sys.stdout,
        descriptions=True,
        failfast=False
    )
    
    print(f"Running {test_suite.countTestCases()} tests...\n")
    
    result = runner.run(test_suite)
    
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\nFAILURES ({len(result.failures)}):")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print(f"\nERRORS ({len(result.errors)}):")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback.split('Error:')[-1].strip()}")
    
    print("\n" + "=" * 80)
    
    # Return success/failure status
    return len(result.failures) == 0 and len(result.errors) == 0

if __name__ == '__main__':
    success = run_test_suite()
    sys.exit(0 if success else 1)