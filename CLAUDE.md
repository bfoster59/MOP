# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a single-file Python 3 application (`MOP.py`) for calculating "Measurement Over Wires" (MOW) for external spur gears using diametral pitch (DP) units. The tool implements precise gear metrology calculations used in CNC machining and gear inspection.

## Core Functionality

The application calculates MOW using involute gear geometry:
- **2-wire method**: For even tooth count gears (measurement across opposite wires)
- **odd tooth method**: For odd tooth count gears (measurement across same-side wire pair)
- **Exact wire size solving**: Uses Newton-Raphson inversion of involute functions
- **Best wire estimation**: Rule-of-thumb wire diameter calculation based on pressure angle

## Usage Modes

### Command Line Interface
```bash
# Single calculation
python MOP.py --z 45 --dp 8 --pa 20 --t 0.2124 --d 0.2160

# Using best wire rule (auto-calculates wire diameter)
python MOP.py --z 45 --dp 8 --pa 20 --t 0.2124 --best-wire rule

# CSV batch processing
python MOP.py --csv-in input.csv --csv-out results.csv --best-wire rule
```

### GUI Mode
```bash
python MOP.py --ui
```
Launches a Tkinter-based GUI with input fields and real-time calculation results.

### CSV Batch Processing
Expected CSV format with columns: `z,dp,pa,t,d` (where `d` is optional if using `--best-wire rule`)

## Key Parameters
- `z`: Tooth count (integer)
- `dp`: Diametral pitch [1/inch] (float)
- `pa`: Pressure angle [degrees] (float)
- `t`: Circular tooth thickness at pitch [inches] (float)
- `d`: Wire diameter [inches] (float, optional with best-wire)

## Mathematical Foundation

The code implements standard involute gear formulas:
- `inv(x) = tan(x) - x` (involute function)
- Newton-Raphson inversion for solving `inv(β) = t/Dp - E + inv(α) + d/Db`
- Method selection based on tooth count parity (even/odd)

## Testing

No formal test suite exists. Manual testing can be done with known gear parameters:
```bash
# Test with typical 45-tooth, 8 DP, 20° PA gear
python MOP.py --z 45 --dp 8 --pa 20 --t 0.2124 --d 0.2160
```

## Dependencies

Uses only Python standard library:
- `math` - Mathematical functions
- `argparse` - Command line parsing
- `csv` - CSV file processing
- `dataclasses` - Result data structure
- `tkinter` - GUI interface (optional)
- `typing` - Type hints

## File Structure

Single-file application with these main sections:
- Involute mathematical functions (`MOP.py:32-45`)
- Core MOW calculation engine (`MOP.py:62-91`)
- Best wire diameter estimation (`MOP.py:94-119`)
- CLI interface (`MOP.py:122-147`)
- CSV batch processing (`MOP.py:148-181`)
- Tkinter GUI (`MOP.py:184-283`)
- Main entry point (`MOP.py:286-318`)