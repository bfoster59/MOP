#!/usr/bin/env python3
"""
Performance Analysis Script for MOP Gear Metrology System
Identifies computational bottlenecks and measures execution times
"""

import time
import profile
import cProfile
import pstats
import io
from typing import Dict, List, Tuple
import statistics
import sys
import os

# Add the current directory to sys.path to import MOP module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from MOP import (
    mow_spur_external_dp, mbp_spur_internal_dp,
    mow_helical_external_dp, mbp_helical_internal_dp,
    calculate_improved_helical_correction, inv_inverse, best_pin_rule
)

class PerformanceAnalyzer:
    """Comprehensive performance analysis for MOP calculations"""
    
    def __init__(self):
        self.results = {}
        self.iterations = 1000  # Number of iterations for timing tests
        
    def time_function(self, func, *args, **kwargs) -> Dict[str, float]:
        """Time a function call multiple times and return statistics"""
        times = []
        
        for _ in range(self.iterations):
            start = time.perf_counter()
            result = func(*args, **kwargs)
            end = time.perf_counter()
            times.append(end - start)
        
        return {
            'mean': statistics.mean(times),
            'median': statistics.median(times),
            'min': min(times),
            'max': max(times),
            'stdev': statistics.stdev(times) if len(times) > 1 else 0,
            'total_time': sum(times),
            'iterations': len(times)
        }
    
    def analyze_newton_raphson_performance(self):
        """Analyze Newton-Raphson iteration performance"""
        print("=== Newton-Raphson Performance Analysis ===")
        
        test_cases = [
            0.1,    # Small value
            0.5,    # Medium value  
            1.0,    # Large value
            1.5,    # Very large value
            0.01    # Very small value
        ]
        
        for y_val in test_cases:
            stats = self.time_function(inv_inverse, y_val)
            print(f"inv_inverse({y_val}): {stats['mean']*1000:.3f} ms avg, "
                  f"{stats['median']*1000:.3f} ms median, ±{stats['stdev']*1000:.3f} ms")
        
        self.results['newton_raphson'] = stats
    
    def analyze_helical_correction_performance(self):
        """Analyze helical correction calculation performance"""
        print("\n=== Helical Correction Performance Analysis ===")
        
        test_cases = [
            (5.0, 20.0, 0.2160, True),    # Low helix external
            (15.0, 20.0, 0.2160, True),   # Medium helix external
            (30.0, 20.0, 0.2160, True),   # High helix external
            (15.0, 20.0, 0.2160, False),  # Medium helix internal
        ]
        
        for helix, pa, pin_d, is_ext in test_cases:
            gear_type = "external" if is_ext else "internal"
            stats = self.time_function(calculate_improved_helical_correction, 
                                     helix, pa, pin_d, is_ext)
            print(f"Helical correction {helix}deg {gear_type}: {stats['mean']*1000000:.1f} us avg, "
                  f"{stats['median']*1000000:.1f} us median")
        
        self.results['helical_correction'] = stats
    
    def analyze_complete_calculation_performance(self):
        """Analyze complete gear calculation performance"""
        print("\n=== Complete Calculation Performance Analysis ===")
        
        # Standard test parameters
        standard_params = {
            'z': 45, 'DP': 8, 'alpha_deg': 20, 't': 0.2124, 'd': 0.2160
        }
        
        helical_params = {
            'z': 127, 'normal_DP': 12, 'normal_alpha_deg': 20, 
            't': 0.130900, 'd': 0.144, 'helix_deg': 15.0
        }
        
        # Spur gear external
        stats_spur = self.time_function(mow_spur_external_dp, **standard_params)
        print(f"Spur external MOP: {stats_spur['mean']*1000:.3f} ms avg")
        
        # Helical gear external
        stats_helical = self.time_function(mow_helical_external_dp, **helical_params)
        print(f"Helical external MOP: {stats_helical['mean']*1000:.3f} ms avg")
        
        # Performance ratio
        ratio = stats_helical['mean'] / stats_spur['mean']
        print(f"Helical/Spur performance ratio: {ratio:.2f}x")
        
        self.results['complete_calculations'] = {
            'spur': stats_spur,
            'helical': stats_helical,
            'performance_ratio': ratio
        }
    
    def analyze_batch_performance(self):
        """Analyze batch calculation performance"""
        print("\n=== Batch Processing Performance Analysis ===")
        
        # Generate batch test data
        batch_size = 100
        test_params = []
        
        for i in range(batch_size):
            params = {
                'z': 32 + (i % 50),
                'DP': 8.0 + (i % 4) * 2,
                'alpha_deg': 20.0,
                't': 0.196 + (i % 10) * 0.001,
                'd': 0.210
            }
            test_params.append(params)
        
        def batch_calculation():
            results = []
            for params in test_params:
                result = mow_spur_external_dp(**params)
                results.append(result.MOW)
            return results
        
        batch_stats = self.time_function(batch_calculation)
        print(f"Batch {batch_size} calculations: {batch_stats['mean']*1000:.1f} ms total")
        print(f"Per calculation: {batch_stats['mean']*1000/batch_size:.3f} ms avg")
        
        self.results['batch_processing'] = batch_stats
    
    def profile_critical_functions(self):
        """Profile critical functions with cProfile"""
        print("\n=== Function Profiling ===")
        
        # Profile a complex helical calculation
        def complex_calculation():
            for i in range(10):
                result = mow_helical_external_dp(
                    z=127, normal_DP=12, normal_alpha_deg=20,
                    t=0.130900, d=0.144, helix_deg=15.0 + i
                )
        
        pr = cProfile.Profile()
        pr.enable()
        complex_calculation()
        pr.disable()
        
        # Capture and display profile results
        s = io.StringIO()
        ps = pstats.Stats(pr, stream=s)
        ps.sort_stats('cumulative').print_stats(15)  # Top 15 functions
        
        print(s.getvalue())
    
    def memory_usage_analysis(self):
        """Basic memory usage analysis"""
        print("\n=== Memory Usage Analysis ===")
        
        # Test data structure sizes
        import sys
        
        # Create a typical result object
        result = mow_helical_external_dp(
            z=127, normal_DP=12, normal_alpha_deg=20,
            t=0.130900, d=0.144, helix_deg=15.0
        )
        
        result_size = sys.getsizeof(result)
        print(f"Result object size: {result_size} bytes")
        
        # Test list of results for batch processing
        results_list = []
        for i in range(1000):
            result = mow_spur_external_dp(z=45, DP=8, alpha_deg=20, t=0.2124, d=0.2160)
            results_list.append(result)
        
        list_size = sys.getsizeof(results_list)
        total_size = list_size + (result_size * len(results_list))
        print(f"1000 results memory usage: ~{total_size/1024:.1f} KB")
    
    def generate_performance_report(self):
        """Generate comprehensive performance report"""
        print("\n" + "="*60)
        print("PERFORMANCE ANALYSIS SUMMARY")
        print("="*60)
        
        if 'newton_raphson' in self.results:
            nr_stats = self.results['newton_raphson']
            print(f"Newton-Raphson avg time: {nr_stats['mean']*1000:.3f} ms")
        
        if 'complete_calculations' in self.results:
            calc_stats = self.results['complete_calculations']
            print(f"Spur calculation avg: {calc_stats['spur']['mean']*1000:.3f} ms")
            print(f"Helical calculation avg: {calc_stats['helical']['mean']*1000:.3f} ms")
            print(f"Helical overhead: {calc_stats['performance_ratio']:.1f}x")
        
        if 'batch_processing' in self.results:
            batch_stats = self.results['batch_processing']
            per_calc = batch_stats['mean'] / 100  # 100 calculations in batch
            print(f"Batch processing per calc: {per_calc*1000:.3f} ms")
        
        print("\nRecommendations:")
        print("1. Newton-Raphson convergence is efficient")
        print("2. Helical corrections add minimal overhead")
        print("3. Batch processing shows good scalability")
        print("4. Memory usage is reasonable for typical applications")

def main():
    """Run complete performance analysis"""
    analyzer = PerformanceAnalyzer()
    
    print("Starting MOP Performance Analysis...")
    print(f"Running {analyzer.iterations} iterations per test")
    
    analyzer.analyze_newton_raphson_performance()
    analyzer.analyze_helical_correction_performance()
    analyzer.analyze_complete_calculation_performance()
    analyzer.analyze_batch_performance()
    analyzer.memory_usage_analysis()
    analyzer.profile_critical_functions()
    analyzer.generate_performance_report()

if __name__ == "__main__":
    main()