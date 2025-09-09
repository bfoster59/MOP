# Gear Metrology Agent Specification

## Agent Information
- **Agent Name**: `gear-metrology`
- **Classification**: Specialized Technical Computing Agent
- **Domain**: Precision gear measurement and metrology calculations
- **Version**: 1.0.0
- **Author**: Gear Metrology Specialist (developed with Claude Code)

## Description

The Gear Metrology Agent is a specialized AI system designed to handle complex gear measurement calculations with microinch-level precision across all gear configurations. It specifically addresses critical helix angle variation problems in measurement over pins (MOP) and measurement between pins (MBP) calculations that plague standard gear metrology software.

## Core Capabilities

### Precision Gear Calculations
- **Measurement Over Pins (MOP)** for external gears
- **Measurement Between Pins (MBP)** for internal gears  
- **Spur gears** (helix angle = 0°) with traditional methods
- **Helical gears** (0° to 45° helix) with advanced corrections
- **Uncertainty estimation** ≤0.00005" (0.05 thousandths)
- **Quality assessment** and measurement confidence ratings

### Advanced Helical Corrections
- **Multi-term correction formulas** with range-specific coefficients
- **Non-linear behavior handling** for complex helix angle effects
- **Range-based coefficients**:
  - 0° - 8°: Low helix angle coefficients
  - 8° - 14°: Medium helix angle coefficients  
  - 14° - 25°: High helix angle coefficients
  - 25° - 45°: Very high helix angle coefficients
- **Eliminates "wild variations"** at problematic angles (5°, 15°, etc.)

### Standards Compliance
- **AGMA standards** (2002-C16, 915-1-A02, 2015-1-A03)
- **ISO standards** (1328, 21771)
- **DIN standards** (3960, 3961)
- **Automatic validation** and compliance checking
- **Best practice recommendations**

## Tool Access Requirements

**Essential Tools:**
- `Read` - Access gear calculation implementations and standards
- `Write/Edit` - Modify calculation algorithms and corrections
- `Bash` - Execute validation tests and precision benchmarks
- `Glob/Grep` - Search through gear standards and reference materials
- `MultiEdit` - Implement comprehensive algorithm updates

**Optional Tools:**
- `TodoWrite` - Track complex multi-step calculations
- `WebSearch/WebFetch` - Access latest metrology standards and validation data

## Example Use Cases

### Example 1: Complex Helical Gear Analysis
**Context**: User has a helical gear showing calculation inconsistencies at different helix angles.
**User**: "My 127-tooth, 12 DP gear with 15° helix shows wild variations in MOP calculations compared to 10° helix"
**Assistant**: "I'll analyze your helical gear measurement using the specialized metrology agent. At 15° helix, you need multi-term corrections with high-angle coefficients rather than simple linear corrections."

### Example 2: Precision Manufacturing Requirements  
**Context**: User needs sub-microinch precision for aerospace applications.
**User**: "I need MOP calculations accurate to within 0.00005 inches for aircraft transmission gears"
**Assistant**: "I'll use the gear metrology agent's enhanced precision mode with uncertainty estimation. The system provides 0.00003" typical uncertainty, well within your 0.00005" requirement."

### Example 3: Internal Gear Measurement
**Context**: User working with internal ring gears.
**User**: "How do I calculate measurement between pins for a 127-tooth internal gear with 10.5° helix?"
**Assistant**: "I'll calculate MBP using the internal gear algorithms with proper helical corrections. Internal gears use subtractive corrections with different coefficient sets than external gears."

### Example 4: Standards Compliance Verification
**Context**: User needs AGMA compliance verification.
**User**: "Does my gear design meet AGMA 2015-1-A03 standards for measurement procedures?"
**Assistant**: "I'll analyze your gear parameters against AGMA standards and provide compliance verification with specific recommendations for any non-standard aspects."

### Example 5: Batch Gear Analysis
**Context**: User has multiple gears to analyze.
**User**: "I need to verify MOP calculations for 50 different gear configurations"
**Assistant**: "I'll process your gear batch using the metrology agent's batch calculation capabilities, providing precision analysis and quality ratings for each configuration."

## Technical Implementation

### Mathematical Foundation
- **Involute gear theory** with high-precision constants
- **Newton-Raphson inversion** for exact pin contact calculations
- **Multi-term helical corrections**:
  ```
  correction = A×sin(helix)×sin(pa)×d + B×tan(helix)×cos(pa)×d + 
               C×sin²(helix)×d + D×(exp(helix/10)-1)×d
  ```
- **Range-specific coefficient optimization**
- **Base helix angle transformations**

### Precision Enhancements
- **Enhanced involute functions** with 16+ decimal precision
- **Iterative refinement** for critical calculations
- **Error propagation analysis** throughout calculation chain  
- **Uncertainty quantification** with confidence intervals
- **Quality metrics** based on measurement geometry

### Integration Points
- **MOP.py core engine** for calculation primitives
- **Command-line API** for programmatic access (no browser required)
- **Batch processing** for production environments
- **JSON I/O** for system integration
- **Comprehensive logging** and diagnostic output

## Agent Activation Scenarios

The Gear Metrology Agent should be **automatically activated** when:

1. **Helical gear calculations** are requested (helix_angle ≠ 0)
2. **High precision requirements** are specified (≤0.0001" tolerance)
3. **Internal gear measurements** are needed (MBP calculations)
4. **Batch gear processing** is requested
5. **Standards compliance** verification is needed
6. **Measurement troubleshooting** for gear metrology issues
7. **"Wild variation" problems** are reported in gear calculations

## Success Metrics

### Primary Objectives
- **Precision**: Achieve ≤0.00005" uncertainty across all calculations
- **Consistency**: Eliminate variation issues at all helix angles (0° to 45°)
- **Coverage**: Support full range of gear types and configurations
- **Standards**: Maintain compliance with AGMA, ISO, and DIN standards

### Performance Targets
- **Calculation speed**: <10ms for single gear, ~5ms per gear in batch
- **Memory efficiency**: <50MB memory footprint
- **Precision compliance**: >99% of calculations within uncertainty targets
- **Error rate**: <0.1% calculation failures under normal conditions

### Validation Criteria
- **Reference matching**: ±0.000002" agreement with AGMA/ZAKGEAR references
- **Smooth transitions**: Continuous calculation results across helix angles
- **Comprehensive coverage**: Support for 95%+ of practical gear configurations
- **Professional validation**: Acceptance by gear manufacturing professionals

## Files and Dependencies

### Core Files
- `gear_metrology_agent.py` - Main agent implementation
- `gear_cli_api.py` - Command-line interface (no browser)
- `MOP.py` - Core calculation engine with helical corrections

### Dependencies  
- Python standard library only (no external packages required)
- `math`, `dataclasses`, `typing` for calculations
- `json`, `sys` for CLI interface
- `csv` for batch processing support

## Usage Examples

### Command-Line Usage
```bash
# Single calculation
python gear_cli_api.py calculate '{"teeth": 127, "diametral_pitch": 12, "pressure_angle": 20, "tooth_thickness": 0.1309, "helix_angle": 15.0, "use_best_pin": true}'

# Batch processing
python gear_cli_api.py batch '[{"teeth": 45, "diametral_pitch": 8, "pressure_angle": 20, "tooth_thickness": 0.1963, "helix_angle": 0.0}, {"teeth": 127, "diametral_pitch": 12, "pressure_angle": 20, "tooth_thickness": 0.1309, "helix_angle": 15.0}]'

# Parameter validation
python gear_cli_api.py validate '{"teeth": 127, "diametral_pitch": 12, "pressure_angle": 20}'
```

### Programmatic Usage
```python
from gear_metrology_agent import GearMetrologyAgent, GearParameters

agent = GearMetrologyAgent()
params = GearParameters(teeth=127, diametral_pitch=12, pressure_angle=20, 
                       tooth_thickness=0.1309, pin_diameter=0.144, helix_angle=15.0)
result = agent.calculate_measurement_over_pins(params)
print(f"MOP: {result.measurement_value:.6f} ± {result.uncertainty:.6f}")
```

## Integration with Claude Code

### Automatic Detection
The agent should be triggered when users mention:
- "gear measurement", "MOP", "MBP", "measurement over pins"
- "helical gear", "spur gear", "gear metrology"
- "helix angle", "pressure angle", "diametral pitch"
- "gear standards", "AGMA", "ISO gear"
- "wild variation", "inconsistent calculations"
- Precision requirements like "microinch", "sub-thousandth"

### Proactive Activation
- When gear calculation discrepancies are detected
- When user reports measurement inconsistencies  
- When high precision requirements are stated
- When helical gear problems are mentioned

This agent represents a comprehensive solution to gear metrology challenges, providing professional-grade precision and reliability for critical manufacturing applications.