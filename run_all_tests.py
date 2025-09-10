#!/usr/bin/env python3
"""
Comprehensive Test Runner for MOP Gear Metrology System
Runs all available test suites and provides summary
"""

import sys
import subprocess
import time
import os

def run_test_script(script_name, description):
    """Run a test script and return results"""
    
    if not os.path.exists(script_name):
        return {
            'name': script_name,
            'description': description,
            'status': 'SKIP',
            'reason': 'File not found',
            'output': '',
            'duration': 0
        }
    
    print(f"\nRunning {description}...")
    print("-" * 50)
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            capture_output=True,
            text=True,
            timeout=60  # 60 second timeout
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        if result.returncode == 0:
            status = 'PASS'
            print("PASSED")
        else:
            status = 'FAIL'
            print("FAILED")
        
        return {
            'name': script_name,
            'description': description,
            'status': status,
            'returncode': result.returncode,
            'output': result.stdout,
            'error': result.stderr,
            'duration': duration
        }
        
    except subprocess.TimeoutExpired:
        return {
            'name': script_name,
            'description': description,
            'status': 'TIMEOUT',
            'reason': 'Test exceeded 60 second timeout',
            'output': '',
            'duration': 60
        }
    except Exception as e:
        return {
            'name': script_name,
            'description': description,
            'status': 'ERROR',
            'reason': str(e),
            'output': '',
            'duration': 0
        }

def main():
    """Main test runner"""
    
    print("=" * 80)
    print("MOP GEAR METROLOGY SYSTEM - COMPREHENSIVE TEST SUITE")
    print("=" * 80)
    print(f"Python version: {sys.version}")
    print(f"Test start time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Define all available test scripts
    test_scripts = [
        ('test_simple.py', 'Basic Helical Gear Functionality Tests'),
        ('test_helical_validation.py', 'Helical Gear Precision Validation'),
        ('test_suite.py', 'Comprehensive Unit Test Suite'),
        ('test_api.py', 'API Integration Tests'),
        ('test_corrected.py', 'Correction Algorithm Tests'),
        ('helical_test.py', 'Helical Range Tests'),
    ]
    
    results = []
    total_duration = 0
    
    # Run each test script
    for script_name, description in test_scripts:
        result = run_test_script(script_name, description)
        results.append(result)
        total_duration += result['duration']
    
    # Generate summary report
    print("\n" + "=" * 80)
    print("TEST EXECUTION SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for r in results if r['status'] == 'PASS')
    failed = sum(1 for r in results if r['status'] == 'FAIL')
    skipped = sum(1 for r in results if r['status'] == 'SKIP')
    errors = sum(1 for r in results if r['status'] == 'ERROR')
    timeouts = sum(1 for r in results if r['status'] == 'TIMEOUT')
    
    print(f"Total test scripts: {len(results)}")
    print(f"Passed:            {passed}")
    print(f"Failed:            {failed}")
    print(f"Skipped:           {skipped}")
    print(f"Errors:            {errors}")
    print(f"Timeouts:          {timeouts}")
    print(f"Total duration:    {total_duration:.2f} seconds")
    print()
    
    # Detailed results
    print("DETAILED RESULTS")
    print("-" * 80)
    
    for result in results:
        status_symbol = {
            'PASS': 'PASS',
            'FAIL': 'FAIL',
            'SKIP': 'SKIP',
            'ERROR': 'ERROR',
            'TIMEOUT': 'TIMEOUT'
        }.get(result['status'], '?')
        
        print(f"{status_symbol:8} {result['name']:25} - {result['description']}")
        
        if result['status'] == 'PASS':
            print(f"         Duration: {result['duration']:.2f}s")
        elif result['status'] == 'FAIL':
            print(f"         Return code: {result.get('returncode', 'N/A')}")
            print(f"         Duration: {result['duration']:.2f}s")
        elif result['status'] in ['SKIP', 'ERROR', 'TIMEOUT']:
            print(f"         Reason: {result.get('reason', 'Unknown')}")
        
        print()
    
    # Overall assessment
    print("OVERALL ASSESSMENT")
    print("-" * 80)
    
    if failed == 0 and errors == 0 and timeouts == 0:
        if passed > 0:
            print("SUCCESS: All executed tests passed!")
            print("The MOP gear metrology system is functioning correctly.")
            if skipped > 0:
                print(f"Note: {skipped} test scripts were skipped (files not found).")
        else:
            print("WARNING: No tests were executed.")
    else:
        print("ISSUES DETECTED:")
        if failed > 0:
            print(f"- {failed} test script(s) failed")
        if errors > 0:
            print(f"- {errors} test script(s) had execution errors")
        if timeouts > 0:
            print(f"- {timeouts} test script(s) timed out")
        
        print("\nRecommendations:")
        print("1. Check individual test outputs for specific issues")
        print("2. Verify all dependencies are installed")
        print("3. Ensure MOP.py and related modules are accessible")
    
    # Quality metrics
    if passed > 0:
        success_rate = (passed / (len(results) - skipped)) * 100 if (len(results) - skipped) > 0 else 0
        print(f"\nSuccess Rate: {success_rate:.1f}% of executable tests")
    
    print("\n" + "=" * 80)
    print("Test execution completed.")
    print(f"End time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Return appropriate exit code
    if failed > 0 or errors > 0 or timeouts > 0:
        return 1
    elif passed == 0:
        return 2  # No tests ran
    else:
        return 0  # Success

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)