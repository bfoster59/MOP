# WORK INSTRUCTION: Measurement Over Wires (MOP) Calculator

**Document Number:** WI-MOP-001  
**Revision:** 1.0  
**Date:** 2025-09-05  
**Purpose:** Calculate Measurement Over Wires for external spur gears using diametral pitch units

---

## 1. SCOPE

This work instruction covers the use of the MOP.py application for calculating measurement over wires (pins) for external spur gears. The application supports both even and odd tooth count gears using 2-wire and odd tooth methods respectively.

## 2. SAFETY & PREREQUISITES

### 2.1 Prerequisites
- Python 3.x installed on the computer
- Access to gear specifications (drawings or inspection sheets)
- Calibrated pin/wire gauges for physical verification

### 2.2 Required Information
Before starting, gather the following gear parameters:
- **z** - Number of teeth
- **DP** - Diametral pitch (teeth per inch of pitch diameter)
- **PA** - Pressure angle in degrees (typically 14.5°, 20°, or 25°)
- **t** - Circular tooth thickness at pitch diameter (inches)
- **d** - Wire/pin diameter (inches) - can be auto-calculated if unknown

## 3. GRAPHICAL USER INTERFACE (GUI) MODE

### 3.1 Starting the GUI

1. Open Command Prompt or Terminal
2. Navigate to the MOP directory:
   ```
   cd C:\CNC\MOP
   ```
3. Launch the GUI:
   ```
   python MOP.py --ui
   ```

### 3.2 GUI Operation Procedure

#### Step 1: Enter Gear Parameters
1. **Teeth (z)**: Enter the total number of teeth
   - Example: `45`
2. **Diametral Pitch (DP)**: Enter the DP value
   - Example: `8` (for 8 DP)
3. **Pressure Angle α (deg)**: Enter the pressure angle
   - Standard values: `14.5`, `20`, or `25`
4. **Tooth Thickness t (in)**: Enter the circular tooth thickness
   - Example: `0.2124`

#### Step 2: Specify Wire Diameter
- **Option A - Manual Entry**:
  1. Enter known wire diameter in the "Wire Diameter d (in)" field
  2. Example: `0.2160`
  
- **Option B - Auto-Calculate**:
  1. Check the "Use best wire (rule-of-thumb)" checkbox
  2. The wire diameter will be automatically calculated based on:
     - 20° PA: d ≈ 1.68/DP
     - 25° PA: d ≈ 1.70/DP
     - 14.5° PA: d ≈ 1.728/DP

#### Step 3: Calculate Results
1. Click the **Compute** button
2. The application will display:
   - **Detected Method**: "2-wire" (even teeth) or "odd tooth" (odd teeth)
   - **MOW**: Measurement over wires value in inches
   - **Additional geometry data** for verification

#### Step 4: Record Results
1. Note the MOW value for inspection purposes
2. Compare with drawing specifications
3. Document in inspection report

### 3.3 GUI Example Walkthrough

**Scenario**: Inspect a 45-tooth, 8 DP gear with 20° pressure angle

1. Launch GUI: `python MOP.py --ui`
2. Enter values:
   - Teeth: `45`
   - DP: `8`
   - Pressure Angle: `20`
   - Tooth Thickness: `0.2124`
   - Check "Use best wire" OR enter `0.2160`
3. Click **Compute**
4. Results show:
   - Method: odd tooth (odd tooth count)
   - MOW: 5.9637 inches
5. Use this value for gear inspection

## 4. COMMAND LINE INTERFACE (CLI) MODE

### 4.1 Basic CLI Syntax

```
python MOP.py --z [teeth] --dp [pitch] --pa [angle] --t [thickness] --d [wire_dia]
```

### 4.2 CLI Operation Procedures

#### Procedure A: Single Calculation with Known Wire

1. Open Command Prompt/Terminal
2. Navigate to MOP directory
3. Run command with all parameters:
   ```
   python MOP.py --z 45 --dp 8 --pa 20 --t 0.2124 --d 0.2160
   ```
4. Review output showing MOW value and calculation details

#### Procedure B: Single Calculation with Auto Wire

1. Use `--best-wire rule` instead of specifying wire diameter:
   ```
   python MOP.py --z 45 --dp 8 --pa 20 --t 0.2124 --best-wire rule
   ```
2. Application calculates optimal wire diameter automatically

#### Procedure C: Batch Processing with CSV

1. **Prepare Input CSV** (input.csv):
   ```csv
   z,dp,pa,t,d
   45,8,20,0.2124,0.2160
   30,10,20,0.1571,
   24,12,25,0.1309,0.1420
   ```
   Note: Leave `d` column empty if using best-wire rule

2. **Run Batch Process**:
   ```
   python MOP.py --csv-in input.csv --csv-out results.csv --best-wire rule
   ```

3. **Review Output CSV** (results.csv):
   - Contains all input parameters
   - MOW calculation results
   - Method used (2-wire or odd tooth)
   - Additional geometry values

### 4.3 CLI Options Reference

| Option | Description | Example |
|--------|-------------|---------|
| `--z` | Number of teeth | `--z 45` |
| `--dp` | Diametral pitch | `--dp 8` |
| `--pa` | Pressure angle (degrees) | `--pa 20` |
| `--t` | Tooth thickness (inches) | `--t 0.2124` |
| `--d` | Wire diameter (inches) | `--d 0.2160` |
| `--best-wire` | Auto-calculate wire | `--best-wire rule` |
| `--digits` | Decimal places for MOW | `--digits 6` |
| `--csv-in` | Input CSV file path | `--csv-in batch.csv` |
| `--csv-out` | Output CSV file path | `--csv-out results.csv` |
| `--ui` | Launch GUI mode | `--ui` |
| `--help` | Show help message | `--help` |

## 5. PRACTICAL EXAMPLES

### Example 1: Even Tooth Count (2-Wire Method)

**Gear**: 30 teeth, 10 DP, 20° PA
```bash
python MOP.py --z 30 --dp 10 --pa 20 --t 0.1571 --best-wire rule
```
- Method: 2-wire (even teeth)
- Wires placed on opposite teeth
- MOW measured directly across wires

### Example 2: Odd Tooth Count (Odd Tooth Method)

**Gear**: 45 teeth, 8 DP, 20° PA
```bash
python MOP.py --z 45 --dp 8 --pa 20 --t 0.2124 --d 0.2160
```
- Method: odd tooth (odd teeth)
- Two wires on same side, one opposite
- Measurement taken across the two same-side wires

### Example 3: High Precision Output

For quality control requiring 6 decimal places:
```bash
python MOP.py --z 24 --dp 12 --pa 25 --t 0.1309 --d 0.1420 --digits 6
```

## 6. MEASUREMENT VERIFICATION

### 6.1 Physical Measurement Procedure

1. **Select Appropriate Wires**:
   - Use the calculated or specified wire diameter
   - Ensure wires are clean and calibrated

2. **For Even Teeth (2-Wire)**:
   - Place wires in tooth spaces 180° apart
   - Measure directly across both wires with micrometer

3. **For Odd Teeth (Odd Tooth Method)**:
   - Place two wires in adjacent tooth spaces
   - Place third wire in opposite tooth space
   - Measure across the two adjacent wires

4. **Compare Results**:
   - Measured value should match calculated MOW ±0.0005"
   - If variance exceeds tolerance, check:
     - Wire diameter accuracy
     - Tooth thickness measurement
     - Gear manufacturing quality

## 7. TROUBLESHOOTING

### Issue: "Missing required args"
**Solution**: Ensure all required parameters (z, dp, pa, t) are provided

### Issue: "All inputs must be positive"
**Solution**: Check that no negative or zero values are entered

### Issue: GUI won't launch
**Solution**: 
1. Ensure tkinter is installed: `python -m tkinter`
2. If missing, install python3-tk package

### Issue: CSV processing fails
**Solution**:
1. Verify CSV header format: `z,dp,pa,t,d`
2. Check for non-numeric values in data rows
3. Ensure file paths are correct

### Issue: MOW value seems incorrect
**Solution**:
1. Verify pressure angle (14.5°, 20°, or 25°)
2. Confirm tooth thickness is at pitch diameter
3. Check wire diameter matches actual pins used
4. Verify diametral pitch (DP) not module

## 8. QUALITY RECORDS

Document the following in inspection reports:
- Date and time of calculation
- Input parameters used
- Calculated MOW value
- Actual measured value
- Pass/Fail status per drawing tolerance
- Inspector name/ID

## 9. REFERENCE FORMULAS

The application uses these key formulas:

- **Pitch Diameter**: Dp = z / DP
- **Base Diameter**: Db = Dp × cos(α)
- **Involute Function**: inv(x) = tan(x) - x
- **Contact Angle β**: Solved from inv(β) = t/Dp - π/z + inv(α) + d/Db
- **2-Wire MOW**: MOW = Db/cos(β) + d
- **Odd Tooth MOW**: MOW = (Db/cos(β)) × cos(π/2z) + d

## 10. REVISION HISTORY

| Rev | Date | Description | Author |
|-----|------|-------------|---------|
| 1.0 | 2025-09-05 | Initial release | QC Dept |

---

**END OF WORK INSTRUCTION**

For technical support, contact the Quality Control Department or Engineering.