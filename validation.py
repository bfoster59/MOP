#!/usr/bin/env python3
"""
Input Validation Module for MOP Gear Metrology System
Comprehensive validation with geometric feasibility checks
"""

import math
from typing import Tuple, Optional, Dict, Any, List
from dataclasses import dataclass

@dataclass
class ValidationResult:
    """Result of input validation"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    sanitized_values: Optional[Dict[str, Any]] = None

class GearValidationError(Exception):
    """Custom exception for gear validation errors"""
    pass

class InputValidator:
    """Comprehensive input validation for gear calculations"""
    
    # Define reasonable bounds for gear parameters
    BOUNDS = {
        'z': (4, 1000),           # Tooth count: 4 to 1000 teeth
        'dp': (0.1, 1000),        # Diametral pitch: 0.1 to 1000 (1/inch)
        'module': (0.025, 25.4),  # Module: 0.025 to 25.4 mm
        'pa': (5.0, 45.0),        # Pressure angle: 5° to 45°
        'helix': (-45.0, 45.0),   # Helix angle: -45° to +45°
        't': (0.001, 100.0),      # Tooth thickness: 0.001 to 100 inches
        's': (0.001, 100.0),      # Space width: 0.001 to 100 inches  
        'd': (0.001, 50.0),       # Pin diameter: 0.001 to 50 inches
    }
    
    # Standard pressure angles for validation warnings
    STANDARD_PRESSURE_ANGLES = [14.5, 17.5, 20.0, 22.5, 25.0, 30.0]
    
    @staticmethod
    def validate_basic_parameters(z: float, dp: float, pa: float, 
                                helix: float = 0.0) -> ValidationResult:
        """Validate basic gear parameters"""
        
        errors = []
        warnings = []
        
        # Convert to appropriate types and check basic bounds
        try:
            z = int(round(z))
            dp = float(dp)
            pa = float(pa) 
            helix = float(helix)
        except (ValueError, TypeError) as e:
            errors.append(f"Parameter type conversion error: {str(e)}")
            return ValidationResult(False, errors, warnings)
        
        # Check individual parameter bounds
        if not (InputValidator.BOUNDS['z'][0] <= z <= InputValidator.BOUNDS['z'][1]):
            errors.append(f"Tooth count z={z} outside valid range {InputValidator.BOUNDS['z']}")
        
        if not (InputValidator.BOUNDS['dp'][0] <= dp <= InputValidator.BOUNDS['dp'][1]):
            errors.append(f"Diametral pitch dp={dp} outside valid range {InputValidator.BOUNDS['dp']}")
        
        if not (InputValidator.BOUNDS['pa'][0] <= pa <= InputValidator.BOUNDS['pa'][1]):
            errors.append(f"Pressure angle pa={pa}° outside valid range {InputValidator.BOUNDS['pa']}")
        
        if not (InputValidator.BOUNDS['helix'][0] <= helix <= InputValidator.BOUNDS['helix'][1]):
            errors.append(f"Helix angle helix={helix}° outside valid range {InputValidator.BOUNDS['helix']}")
        
        # Check for standard pressure angles
        if abs(pa - min(InputValidator.STANDARD_PRESSURE_ANGLES, key=lambda x: abs(x - pa))) > 2.5:
            warnings.append(f"Non-standard pressure angle {pa}°. Standard angles: {InputValidator.STANDARD_PRESSURE_ANGLES}")
        
        # Geometric feasibility checks
        if len(errors) == 0:  # Only if basic parameters are valid
            # Check if gear is physically realizable
            pitch_diameter = z / dp
            
            if pitch_diameter < 0.1:
                warnings.append(f"Very small pitch diameter {pitch_diameter:.3f}\" may be impractical")
            elif pitch_diameter > 100.0:
                warnings.append(f"Very large pitch diameter {pitch_diameter:.1f}\" may be impractical")
            
            # Check for reasonable module size (for reference)
            module_mm = 25.4 / dp
            if module_mm < 0.5:
                warnings.append(f"Very fine module {module_mm:.2f}mm may be difficult to manufacture")
            elif module_mm > 20:
                warnings.append(f"Very coarse module {module_mm:.1f}mm may be unusual")
        
        sanitized = {
            'z': z,
            'dp': dp, 
            'pa': pa,
            'helix': helix
        }
        
        return ValidationResult(len(errors) == 0, errors, warnings, sanitized)
    
    @staticmethod
    def validate_tooth_thickness(t: float, dp: float, z: int) -> ValidationResult:
        """Validate tooth thickness for geometric feasibility"""
        
        errors = []
        warnings = []
        
        try:
            t = float(t)
            dp = float(dp)
            z = int(z)
        except (ValueError, TypeError) as e:
            errors.append(f"Parameter type conversion error: {str(e)}")
            return ValidationResult(False, errors, warnings)
        
        # Check bounds
        if not (InputValidator.BOUNDS['t'][0] <= t <= InputValidator.BOUNDS['t'][1]):
            errors.append(f"Tooth thickness t={t} outside valid range {InputValidator.BOUNDS['t']}")
            return ValidationResult(False, errors, warnings)
        
        # Geometric checks
        circular_pitch = math.pi / dp
        standard_thickness = circular_pitch / 2.0
        
        # Tooth thickness should not exceed circular pitch
        if t >= circular_pitch:
            errors.append(f"Tooth thickness {t:.6f}\" exceeds circular pitch {circular_pitch:.6f}\"")
        
        # Check for reasonable thickness ratio
        thickness_ratio = t / standard_thickness
        if thickness_ratio < 0.3:
            warnings.append(f"Very thin tooth (ratio {thickness_ratio:.2f}) may be weak")
        elif thickness_ratio > 1.7:
            warnings.append(f"Very thick tooth (ratio {thickness_ratio:.2f}) may cause interference")
        
        sanitized = {'t': t}
        return ValidationResult(len(errors) == 0, errors, warnings, sanitized)
    
    @staticmethod
    def validate_space_width(s: float, dp: float, z: int) -> ValidationResult:
        """Validate space width for internal gears"""
        
        errors = []
        warnings = []
        
        try:
            s = float(s)
            dp = float(dp)
            z = int(z)
        except (ValueError, TypeError) as e:
            errors.append(f"Parameter type conversion error: {str(e)}")
            return ValidationResult(False, errors, warnings)
        
        # Check bounds
        if not (InputValidator.BOUNDS['s'][0] <= s <= InputValidator.BOUNDS['s'][1]):
            errors.append(f"Space width s={s} outside valid range {InputValidator.BOUNDS['s']}")
            return ValidationResult(False, errors, warnings)
        
        # Geometric checks for internal gears
        circular_pitch = math.pi / dp
        standard_space = circular_pitch / 2.0
        
        # Space width should not exceed circular pitch
        if s >= circular_pitch:
            errors.append(f"Space width {s:.6f}\" exceeds circular pitch {circular_pitch:.6f}\"")
        
        # Check for reasonable space ratio
        space_ratio = s / standard_space
        if space_ratio < 0.3:
            warnings.append(f"Very narrow space (ratio {space_ratio:.2f}) may cause manufacturing issues")
        elif space_ratio > 1.7:
            warnings.append(f"Very wide space (ratio {space_ratio:.2f}) may affect gear mesh")
        
        sanitized = {'s': s}
        return ValidationResult(len(errors) == 0, errors, warnings, sanitized)
    
    @staticmethod
    def validate_pin_diameter(d: float, dp: float, pa: float) -> ValidationResult:
        """Validate pin diameter for measurement feasibility"""
        
        errors = []
        warnings = []
        
        try:
            d = float(d)
            dp = float(dp)
            pa = float(pa)
        except (ValueError, TypeError) as e:
            errors.append(f"Parameter type conversion error: {str(e)}")
            return ValidationResult(False, errors, warnings)
        
        # Check bounds
        if not (InputValidator.BOUNDS['d'][0] <= d <= InputValidator.BOUNDS['d'][1]):
            errors.append(f"Pin diameter d={d} outside valid range {InputValidator.BOUNDS['d']}")
            return ValidationResult(False, errors, warnings)
        
        # Calculate best pin diameter for comparison
        best_pin = 1.728 / dp if abs(pa - 20.0) < 1.0 else 1.68 / dp
        
        # Pin should be reasonable compared to best pin
        pin_ratio = d / best_pin
        if pin_ratio < 0.5:
            warnings.append(f"Pin diameter {d:.4f}\" is {pin_ratio:.2f}x best pin, may be too small")
        elif pin_ratio > 2.0:
            warnings.append(f"Pin diameter {d:.4f}\" is {pin_ratio:.2f}x best pin, may be too large")
        
        # Check if pin is physically realizable
        if d < 0.005:  # 0.005" = 0.127mm
            warnings.append(f"Very small pin diameter {d:.4f}\" may be difficult to manufacture")
        
        sanitized = {'d': d}
        return ValidationResult(len(errors) == 0, errors, warnings, sanitized)
    
    @staticmethod
    def validate_complete_external_gear(z: int, dp: float, pa: float, t: float, 
                                      d: float, helix: float = 0.0) -> ValidationResult:
        """Comprehensive validation for external gear parameters"""
        
        all_errors = []
        all_warnings = []
        sanitized = {}
        
        # Validate basic parameters
        basic_result = InputValidator.validate_basic_parameters(z, dp, pa, helix)
        all_errors.extend(basic_result.errors)
        all_warnings.extend(basic_result.warnings)
        if basic_result.sanitized:
            sanitized.update(basic_result.sanitized)
        
        # If basic validation fails, don't continue
        if not basic_result.is_valid:
            return ValidationResult(False, all_errors, all_warnings, sanitized)
        
        # Validate tooth thickness
        thickness_result = InputValidator.validate_tooth_thickness(t, dp, z)
        all_errors.extend(thickness_result.errors)
        all_warnings.extend(thickness_result.warnings)
        if thickness_result.sanitized:
            sanitized.update(thickness_result.sanitized)
        
        # Validate pin diameter
        pin_result = InputValidator.validate_pin_diameter(d, dp, pa)
        all_errors.extend(pin_result.errors)
        all_warnings.extend(pin_result.warnings)
        if pin_result.sanitized:
            sanitized.update(pin_result.sanitized)
        
        # Additional cross-parameter validation
        if len(all_errors) == 0:
            # Check for potential measurement interference
            pitch_diameter = z / dp
            addendum = 1.0 / dp  # Standard addendum
            outside_diameter = pitch_diameter + 2 * addendum
            
            if d > outside_diameter / 4:
                all_warnings.append(f"Large pin diameter {d:.4f}\" relative to gear size may affect measurement")
        
        return ValidationResult(len(all_errors) == 0, all_errors, all_warnings, sanitized)
    
    @staticmethod
    def validate_complete_internal_gear(z: int, dp: float, pa: float, s: float,
                                      d: float, helix: float = 0.0) -> ValidationResult:
        """Comprehensive validation for internal gear parameters"""
        
        all_errors = []
        all_warnings = []
        sanitized = {}
        
        # Validate basic parameters
        basic_result = InputValidator.validate_basic_parameters(z, dp, pa, helix)
        all_errors.extend(basic_result.errors)
        all_warnings.extend(basic_result.warnings)
        if basic_result.sanitized:
            sanitized.update(basic_result.sanitized)
        
        # If basic validation fails, don't continue
        if not basic_result.is_valid:
            return ValidationResult(False, all_errors, all_warnings, sanitized)
        
        # Validate space width
        space_result = InputValidator.validate_space_width(s, dp, z)
        all_errors.extend(space_result.errors)
        all_warnings.extend(space_result.warnings)
        if space_result.sanitized:
            sanitized.update(space_result.sanitized)
        
        # Validate pin diameter  
        pin_result = InputValidator.validate_pin_diameter(d, dp, pa)
        all_errors.extend(pin_result.errors)
        all_warnings.extend(pin_result.warnings)
        if pin_result.sanitized:
            sanitized.update(pin_result.sanitized)
        
        # Internal gear specific checks
        if len(all_errors) == 0:
            # Internal gears need minimum tooth count for practical manufacturing
            if z < 12:
                all_warnings.append(f"Internal gear with {z} teeth may be difficult to manufacture")
            
            # Check for reasonable internal diameter
            pitch_diameter = z / dp
            dedendum = 1.25 / dp  # Standard dedendum for internal gears
            internal_diameter = pitch_diameter - 2 * dedendum
            
            if internal_diameter < 0.5:
                all_warnings.append(f"Very small internal diameter {internal_diameter:.3f}\" may be impractical")
        
        return ValidationResult(len(all_errors) == 0, all_errors, all_warnings, sanitized)
    
    @staticmethod
    def sanitize_file_path(file_path: str) -> str:
        """Sanitize file path to prevent directory traversal"""
        
        if not isinstance(file_path, str):
            raise GearValidationError("File path must be a string")
        
        # Remove dangerous characters and sequences
        import os
        file_path = os.path.normpath(file_path)
        
        # Prevent directory traversal
        if '..' in file_path or file_path.startswith('/') or ':' in file_path:
            raise GearValidationError("Invalid file path: directory traversal not allowed")
        
        # Ensure reasonable length
        if len(file_path) > 255:
            raise GearValidationError("File path too long")
        
        # Check for valid file extensions
        allowed_extensions = ['.csv', '.txt', '.json']
        if not any(file_path.lower().endswith(ext) for ext in allowed_extensions):
            raise GearValidationError(f"File extension not allowed. Allowed: {allowed_extensions}")
        
        return file_path

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safe division with zero check"""
    if abs(denominator) < 1e-15:  # Effective zero for floating point
        if default is None:
            raise GearValidationError(f"Division by zero: {numerator} / {denominator}")
        return default
    return numerator / denominator

def safe_sqrt(value: float) -> float:
    """Safe square root with negative check"""
    if value < 0:
        raise GearValidationError(f"Cannot take square root of negative number: {value}")
    return math.sqrt(value)

def safe_acos(value: float) -> float:
    """Safe arccosine with domain check"""
    if not (-1.0 <= value <= 1.0):
        raise GearValidationError(f"Arccosine input {value} outside valid domain [-1, 1]")
    return math.acos(value)

def safe_asin(value: float) -> float:
    """Safe arcsine with domain check"""
    if not (-1.0 <= value <= 1.0):
        raise GearValidationError(f"Arcsine input {value} outside valid domain [-1, 1]")
    return math.asin(value)

# Example usage and testing
if __name__ == '__main__':
    # Test validation functions
    print("Testing Input Validation Module")
    print("=" * 40)
    
    # Test external gear validation
    result = InputValidator.validate_complete_external_gear(
        z=32, dp=8, pa=20.0, t=0.2124, d=0.2160, helix=15.0
    )
    
    print(f"External gear validation: {'PASS' if result.is_valid else 'FAIL'}")
    if result.errors:
        print(f"Errors: {result.errors}")
    if result.warnings:
        print(f"Warnings: {result.warnings}")
    
    # Test internal gear validation
    result = InputValidator.validate_complete_internal_gear(
        z=36, dp=12, pa=20.0, s=0.13090, d=0.14000
    )
    
    print(f"Internal gear validation: {'PASS' if result.is_valid else 'FAIL'}")
    if result.errors:
        print(f"Errors: {result.errors}")
    if result.warnings:
        print(f"Warnings: {result.warnings}")
    
    # Test invalid parameters
    result = InputValidator.validate_complete_external_gear(
        z=2, dp=-5, pa=60.0, t=10.0, d=100.0
    )
    
    print(f"Invalid parameters test: {'FAIL' if not result.is_valid else 'ERROR - should fail'}")
    print(f"Errors found: {len(result.errors)}")
    print(f"Warnings found: {len(result.warnings)}")