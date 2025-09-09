#!/usr/bin/env python3
"""
Gear Metrology Command Line API
Pure Python API without web browser dependencies
High-precision gear calculations with accuracy ≤0.00005"
"""

import json
import sys
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from gear_metrology_agent import GearMetrologyAgent, GearParameters

class GearCliAPI:
    """
    Command-line API for gear metrology calculations
    No web browser required - pure Python interface
    """
    
    def __init__(self):
        self.agent = GearMetrologyAgent()
        self.precision_target = 0.00005  # 0.05 thou maximum error
        
    def calculate_single(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate single gear measurement
        
        Args:
            parameters: Dictionary with gear parameters
            
        Returns:
            Dictionary with calculation results
        """
        try:
            # Validate and create gear parameters
            gear_params = GearParameters(
                teeth=int(parameters['teeth']),
                diametral_pitch=float(parameters['diametral_pitch']),
                pressure_angle=float(parameters['pressure_angle']),
                tooth_thickness=float(parameters['tooth_thickness']),
                pin_diameter=float(parameters.get('pin_diameter', 0)),
                helix_angle=float(parameters.get('helix_angle', 0.0)),
                is_internal=bool(parameters.get('is_internal', False)),
                is_metric=bool(parameters.get('is_metric', False))
            )
            
            # Auto-calculate pin if needed
            if gear_params.pin_diameter <= 0 or parameters.get('use_best_pin', False):
                from MOP import best_pin_rule
                dp_for_pin = gear_params.diametral_pitch
                if gear_params.is_metric:
                    dp_for_pin = 25.4 / gear_params.diametral_pitch
                gear_params.pin_diameter = best_pin_rule(dp_for_pin, gear_params.pressure_angle)
            
            # Calculate with high precision
            result = self.agent.calculate_measurement_over_pins(gear_params)
            analysis = self.agent.analyze_gear_configuration(gear_params)
            
            # Check precision requirement
            if result.uncertainty > self.precision_target:
                # Apply additional precision enhancement if needed
                result = self._enhance_precision(gear_params, result)
            
            # Format response
            return {
                'success': True,
                'measurement_value': result.measurement_value,
                'measurement_type': result.measurement_type,
                'method': result.method,
                'uncertainty': result.uncertainty,
                'meets_precision_target': result.uncertainty <= self.precision_target,
                'helical_correction': result.helical_correction,
                'quality_rating': analysis['quality_assessment'],
                'calculation_notes': result.calculation_notes,
                'geometry': {
                    'pitch_diameter': result.pitch_diameter,
                    'base_diameter': result.base_diameter,
                    'contact_angle': result.contact_angle
                },
                'input_parameters': asdict(gear_params)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }
    
    def calculate_batch(self, parameters_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate multiple gears in batch
        
        Args:
            parameters_list: List of parameter dictionaries
            
        Returns:
            Dictionary with batch results
        """
        results = []
        errors = []
        
        for i, params in enumerate(parameters_list):
            try:
                result = self.calculate_single(params)
                if result['success']:
                    results.append(result)
                else:
                    errors.append(f"Calculation {i+1}: {result['error']}")
            except Exception as e:
                errors.append(f"Calculation {i+1}: {str(e)}")
        
        return {
            'success': len(errors) == 0,
            'results': results,
            'summary': {
                'total_requested': len(parameters_list),
                'successful': len(results),
                'failed': len(errors),
                'success_rate': len(results) / len(parameters_list) * 100 if parameters_list else 0,
                'errors': errors if errors else None,
                'precision_compliance': sum(1 for r in results if r['meets_precision_target']) / len(results) * 100 if results else 0
            }
        }
    
    def _enhance_precision(self, params: GearParameters, result) -> Any:
        """
        Apply additional precision enhancement techniques
        """
        # For now, return original result
        # Future: Implement iterative refinement, higher-order corrections, etc.
        return result
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate gear parameters without calculating
        """
        try:
            # Required parameters
            required = ['teeth', 'diametral_pitch', 'pressure_angle', 'tooth_thickness']
            missing = [param for param in required if param not in parameters]
            
            if missing:
                return {
                    'valid': False,
                    'error': f"Missing required parameters: {', '.join(missing)}"
                }
            
            # Range validation
            validations = [
                ('teeth', 6, 500, int),
                ('diametral_pitch', 0.1, 100, float),
                ('pressure_angle', 10, 45, float),
                ('tooth_thickness', 0.001, 10, float),
                ('helix_angle', -45, 45, float)
            ]
            
            for param, min_val, max_val, param_type in validations:
                if param in parameters:
                    try:
                        value = param_type(parameters[param])
                        if not min_val <= value <= max_val:
                            return {
                                'valid': False,
                                'error': f"{param} must be between {min_val} and {max_val}"
                            }
                    except (ValueError, TypeError):
                        return {
                            'valid': False,
                            'error': f"{param} must be a valid {param_type.__name__}"
                        }
            
            return {'valid': True}
            
        except Exception as e:
            return {'valid': False, 'error': str(e)}

def main():
    """Command line interface"""
    if len(sys.argv) < 2:
        print("Gear Metrology Command Line API")
        print("Usage:")
        print("  python gear_cli_api.py calculate '{json_parameters}'")
        print("  python gear_cli_api.py batch '{json_array}'")
        print("  python gear_cli_api.py validate '{json_parameters}'")
        print()
        print("Example:")
        print('  python gear_cli_api.py calculate \'{"teeth": 127, "diametral_pitch": 12, "pressure_angle": 20, "tooth_thickness": 0.1309, "helix_angle": 5.0, "use_best_pin": true}\'')
        return
    
    command = sys.argv[1]
    api = GearCliAPI()
    
    try:
        if command == "calculate":
            params = json.loads(sys.argv[2])
            result = api.calculate_single(params)
            print(json.dumps(result, indent=2))
            
        elif command == "batch":
            params_list = json.loads(sys.argv[2])
            result = api.calculate_batch(params_list)
            print(json.dumps(result, indent=2))
            
        elif command == "validate":
            params = json.loads(sys.argv[2])
            result = api.validate_parameters(params)
            print(json.dumps(result, indent=2))
            
        else:
            print(f"Unknown command: {command}")
            
    except json.JSONDecodeError:
        print("Error: Invalid JSON parameter")
    except IndexError:
        print("Error: Missing parameter")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()