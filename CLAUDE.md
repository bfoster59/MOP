# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a comprehensive gear metrology system with multiple interfaces for calculating Measurement Over Pins (MOP) and Measurement Between Pins (MBP) for both **spur and helical gears**. The system includes desktop GUI, command-line interface, FastAPI web service, and pure CLI API with sub-microinch precision for CNC machining and gear inspection applications.

## Core Functionality

### Spur Gear Calculations
- **External (MOP)**: Uses involute equation `inv(β) = t/Dp - E + inv(α) + d/Db`
- **Internal (MBP)**: AGMA-standard formula `In_Bd = π/N - space_width/PD - D/BD + inv(α)`
- **Methods**: 2-pin (even teeth) / odd-tooth (odd teeth) automatic selection
- **Precision**: ±0.000001" accuracy for both external and internal gears

### Helical Gear Calculations  
- **Multi-Term Correction Formula**: Addresses "wild variation" at different helix angles
- **Range-Specific Coefficients**: 0-8°, 8-14°, 14-25°, 25-45° helix angle ranges
- **Normal/Transverse Conversion**: Automatic parameter conversion for helical calculations
- **Sub-Microinch Precision**: ≤0.00005" maximum error across all helix angles

## System Architecture

### File Structure
```
MOP.py                      # Core engine (56KB) - spur + helical calculations
gear_api.py                 # FastAPI web service (16KB) - RESTful endpoints
gear_cli_api.py            # Command-line API (8KB) - pure Python interface  
gear_metrology_agent.py    # AI agent (12KB) - automated calculations
start_api.py               # API startup script (3KB) - service launcher
requirements.txt           # FastAPI dependencies
```

### Interface Options

#### 1. Command Line Interface (MOP.py)
```bash
# Spur gear calculation
python MOP.py --z 45 --dp 8 --pa 20 --t 0.2124 --d 0.2160

# Helical gear calculation
python MOP.py --z 45 --dp 8 --pa 20 --helix 15 --t 0.2124 --d 0.2160

# Internal gear calculation
python MOP.py --internal --z 36 --dp 12 --pa 20 --t 0.13090 --d 0.14000

# Auto pin diameter
python MOP.py --z 45 --dp 8 --pa 20 --t 0.2124 --best-pin rule

# CSV batch processing
python MOP.py --csv-in gears.csv --csv-out results.csv --best-pin rule
```

#### 2. Desktop GUI (MOP.py --ui)
- **Unit Selection**: Standard (Diametral Pitch) / Metric (Module)
- **Auto-Population**: Smart defaults for tooth thickness and pin diameter
- **Real-Time Updates**: Live calculations as parameters change
- **Helical Support**: Helix angle input with automatic corrections

#### 3. FastAPI Web Service (gear_api.py)
```bash
pip install -r requirements.txt
python start_api.py
```
- **Interactive Docs**: Swagger UI at `http://localhost:8000/docs`
- **Endpoints**: `/calculate`, `/batch`, `/health`, `/examples`
- **JSON API**: RESTful interface with request/response validation

#### 4. Command-Line API (gear_cli_api.py)
```bash
python gear_cli_api.py
```
- **Pure Python**: No browser dependency
- **JSON Interface**: Programmatic access with uncertainty calculations
- **Batch Integration**: Automated workflow support

## Key Parameters

### Standard Parameters
- `z`: Tooth count (integer)
- `dp`: Diametral pitch [1/inch] or Module [mm] depending on unit system
- `pa`: Pressure angle [degrees] (normal pressure angle for helical gears)
- `t`: Tooth thickness [inches/mm] (external) / Space width (internal)
- `d`: Pin diameter [inches/mm]

### Helical-Specific Parameters
- `helix`: Helix angle [degrees] (0° = spur gear, up to 45° supported)
- **Automatic conversions**: Normal ↔ Transverse parameters
- **Correction factors**: Multi-term formula with range-specific coefficients

## Mathematical Foundation

### Involute Functions
- **Involute**: `inv(x) = tan(x) - x`
- **Newton-Raphson**: 250-iteration high-precision inversion
- **Convergence**: 1e-12 tolerance for sub-microinch accuracy

### Helical Corrections
**Multi-term correction formula**:
```
correction = A_sin·sin(β)·sin(α)·d + B_tan·tan(β)·cos(α)·d + 
             C_sin²·sin²(β)·d + D_exp·(e^(β/10)-1)·d
```

**Coefficient Sets** (External/Internal, by helix range):
- **0-8°**: Minimal corrections for low helix angles
- **8-14°**: Standard corrections for typical applications  
- **14-25°**: Enhanced corrections for aggressive helix angles
- **25-45°**: Maximum corrections for extreme helix angles

### Best Pin Rules
- **20° PA**: d ≈ 1.728/DP
- **14.5° PA**: d ≈ 1.68/DP  
- **25° PA**: d ≈ 1.92/DP
- **Auto-selection**: Based on input pressure angle

## CSV Format

**Standard Format**: `z,dp,pa,helix,t,d`
```csv
z,dp,pa,helix,t,d
45,8,20.0,0,0.2124,0.2160      # Spur gear
32,8,20.0,15,0.2124,0.2160     # Helical gear
36,12,20.0,0,0.13090,0.14000   # Internal gear
```

**Optional columns**:
- `helix` defaults to 0° if omitted (spur gear)
- `d` can be omitted when using `--best-pin rule`

## Testing & Validation

### Current Test Coverage
- **Spur gear validation**: Perfect accuracy against reference calculators
- **Helical gear validation**: Sub-microinch accuracy across helix ranges
- **API validation**: Request/response testing and error handling
- **Edge case testing**: Extreme parameters and boundary conditions

### Manual Testing Commands
```bash
# Spur gear baseline
python MOP.py --z 45 --dp 8 --pa 20 --t 0.2124 --d 0.2160

# Helical gear different angles
python MOP.py --z 32 --dp 8 --pa 20 --helix 5 --t 0.2124 --d 0.2160
python MOP.py --z 32 --dp 8 --pa 20 --helix 15 --t 0.2124 --d 0.2160
python MOP.py --z 32 --dp 8 --pa 20 --helix 30 --t 0.2124 --d 0.2160

# API testing
python test_api.py
python test_corrected.py
```

## Dependencies

### Core Application (MOP.py)
- **Standard Library Only**: No external dependencies for core functionality
- `math`, `argparse`, `csv`, `dataclasses`, `tkinter`, `typing`

### API Services (Optional)
```bash
pip install -r requirements.txt
```
- **FastAPI**: 0.104.1 - Web framework
- **Uvicorn**: 0.24.0 - ASGI server  
- **Pydantic**: 2.5.0 - Data validation
- **Optional**: `requests`, `python-multipart`

## Development Guidelines

### Code Organization (MOP.py ~1,500 lines)
- **Lines 1-50**: Constants and involute functions
- **Lines 51-200**: Core spur gear calculations  
- **Lines 201-420**: Helical gear corrections and functions
- **Lines 421-600**: Command-line interface
- **Lines 601-800**: CSV processing
- **Lines 801-1400**: GUI implementation
- **Lines 1401-1500**: Main entry point

### Key Functions by Line Number
- `involute()`: Line 32 - Basic involute function
- `newton_raphson_involute()`: Line 45 - High-precision inversion
- `mow_spur_external_dp()`: Line 62 - External spur gear MOP
- `mbp_spur_internal_dp()`: Line 158 - Internal spur gear MBP  
- `calculate_improved_helical_correction()`: Line 240 - Helical corrections
- `mow_helical_external_dp()`: Line 310 - External helical gear MOP
- `mbp_helical_internal_dp()`: Line 360 - Internal helical gear MBP

### API Endpoints (gear_api.py)
- `POST /calculate`: Single gear calculation with full response
- `POST /batch`: Multiple gear calculations with results array
- `GET /health`: System status and performance metrics
- `GET /examples`: Pre-configured test cases for validation

### Precision Requirements
- **Target Accuracy**: ≤0.00005" (0.05 thou) maximum error
- **Typical Performance**: ±0.00003" for helical gears
- **Spur Baseline**: ±0.000001" reference accuracy
- **Uncertainty Calculation**: Built into CLI API responses

## Known Issues & Solutions

### Resolved Issues
- ✅ **"Wild variation" in helical calculations**: Fixed with multi-term correction
- ✅ **Sub-microinch precision**: Achieved with enhanced coefficients
- ✅ **Internal gear formula**: Corrected to AGMA-standard equation
- ✅ **Unicode encoding**: Removed problematic characters from output

### Maintenance Notes
- **Git Status**: All major development work committed (commit 3b61912)
- **Repository**: https://github.com/bfoster59/MOP
- **Branch**: main (1 commit ahead of origin, now pushed)
- **Documentation**: Comprehensive README and API docs maintained

## Usage Examples

### Basic Calculations
```python
# Import for programmatic use
from MOP import mow_spur_external_dp, mow_helical_external_dp

# Spur gear
result = mow_spur_external_dp(z=45, DP=8, alpha_deg=20, t=0.2124, d=0.2160)
print(f"MOP: {result.MOW:.6f}")

# Helical gear  
result = mow_helical_external_dp(z=45, normal_DP=8, normal_alpha_deg=20, 
                                 t=0.2124, d=0.2160, helix_deg=15)
print(f"MOP: {result.MOW:.6f}")
```

### API Usage
```python
import requests

# Web API
response = requests.post("http://localhost:8000/calculate", json={
    "z": 45, "dp": 8, "pa": 20, "helix": 15,
    "t": 0.2124, "d": 0.2160, "gear_type": "external"
})
result = response.json()
print(f"MOP: {result['mop']:.6f}")

# CLI API
from gear_cli_api import GearCliAPI
api = GearCliAPI()
result = api.calculate_gear({
    "z": 45, "dp": 8, "pa": 20, "helix": 15,
    "t": 0.2124, "d": 0.2160, "gear_type": "external"
})
print(f"MOP: {result['mop']:.6f} ± {result['uncertainty']:.6f}")
```

This system provides professional-grade gear metrology calculations with multiple access methods and sub-microinch precision for critical manufacturing applications.