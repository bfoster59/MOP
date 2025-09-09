#!/usr/bin/env python3
"""
Gear Metrology API
FastAPI web service for precision gear measurement calculations

Features:
- REST API for MOP/MBP calculations
- Interactive documentation (Swagger/OpenAPI)
- Comprehensive validation and error handling
- Integration with improved helical corrections
- Support for batch calculations
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
import uvicorn
from contextlib import asynccontextmanager

# Import our gear calculation modules
from MOP import mow_helical_external_dp, mbp_helical_internal_dp, mow_spur_external_dp, mbp_spur_internal_dp, best_pin_rule
from gear_metrology_agent import GearMetrologyAgent, GearParameters

# Pydantic models for API requests/responses
class GearCalculationRequest(BaseModel):
    """Request model for gear calculations"""
    teeth: int = Field(..., ge=6, le=500, description="Number of teeth (6-500)")
    diametral_pitch: float = Field(..., gt=0, le=100, description="Diametral pitch [1/inch] or Module [mm]")
    pressure_angle: float = Field(..., ge=10, le=45, description="Pressure angle [degrees]")
    tooth_thickness: float = Field(..., gt=0, description="Tooth thickness [inches] (or space width for internal)")
    pin_diameter: Optional[float] = Field(None, gt=0, description="Pin diameter [inches] (auto-calculated if not provided)")
    helix_angle: float = Field(0.0, ge=-45, le=45, description="Helix angle [degrees]")
    is_internal: bool = Field(False, description="True for internal gears (MBP), False for external (MOP)")
    is_metric: bool = Field(False, description="True for module units, False for diametral pitch")
    use_best_pin: bool = Field(False, description="Auto-calculate optimal pin diameter")

    @validator('teeth')
    def validate_teeth(cls, v):
        if v < 6:
            raise ValueError('Minimum tooth count is 6')
        if v > 500:
            raise ValueError('Maximum tooth count is 500')
        return v

    @validator('pressure_angle')
    def validate_pressure_angle(cls, v):
        if not 10 <= v <= 45:
            raise ValueError('Pressure angle must be between 10° and 45°')
        return v

class BatchCalculationRequest(BaseModel):
    """Request model for batch calculations"""
    calculations: List[GearCalculationRequest] = Field(..., max_items=50, description="List of calculations (max 50)")

class GearCalculationResult(BaseModel):
    """Response model for gear calculations"""
    measurement_value: float = Field(..., description="MOP or MBP result [inches]")
    measurement_type: str = Field(..., description="MOP (external) or MBP (internal)")
    method: str = Field(..., description="Measurement method (2-pin or odd tooth)")
    uncertainty: float = Field(..., description="Estimated measurement uncertainty [inches]")
    
    # Input parameters (for reference)
    input_parameters: GearCalculationRequest
    
    # Derived geometry
    pitch_diameter: float = Field(..., description="Pitch diameter [inches]")
    base_diameter: float = Field(..., description="Base diameter [inches]")
    contact_angle: float = Field(..., description="Contact angle at pin [degrees]")
    
    # Helical corrections (if applicable)
    helical_correction: float = Field(0.0, description="Helical correction applied [inches]")
    coefficient_set: Optional[str] = Field(None, description="Coefficient range used for helical correction")
    
    # Quality assessment
    quality_rating: str = Field(..., description="Measurement quality rating")
    calculation_notes: List[str] = Field(default_factory=list, description="Calculation notes and warnings")

class BatchCalculationResult(BaseModel):
    """Response model for batch calculations"""
    results: List[GearCalculationResult]
    summary: Dict[str, Any]

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    features: List[str]

# Initialize FastAPI app
app = FastAPI(
    title="Gear Metrology API",
    description="Precision gear measurement calculations with advanced helical corrections",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Global gear metrology agent instance
gear_agent: Optional[GearMetrologyAgent] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup the gear metrology agent"""
    global gear_agent
    gear_agent = GearMetrologyAgent()
    print("🚀 Gear Metrology API started - Agent initialized")
    yield
    print("🛑 Gear Metrology API shutting down")

app.router.lifespan_context = lifespan

@app.get("/", response_class=HTMLResponse)
async def root():
    """API landing page with quick start guide"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Gear Metrology API</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }
            .container { max-width: 800px; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
            h2 { color: #34495e; margin-top: 30px; }
            .endpoint { background: #ecf0f1; padding: 15px; border-left: 4px solid #3498db; margin: 10px 0; border-radius: 5px; }
            .method { font-weight: bold; color: #27ae60; }
            code { background: #f8f9fa; padding: 2px 5px; border-radius: 3px; font-family: 'Courier New', monospace; }
            .feature { margin: 5px 0; }
            .feature:before { content: "✓ "; color: #27ae60; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔧 Gear Metrology API</h1>
            <p>Precision gear measurement calculations with advanced helical corrections</p>
            
            <h2>🚀 Quick Start</h2>
            <div class="endpoint">
                <div class="method">GET</div>
                <code>/docs</code> - Interactive API documentation (Swagger UI)
            </div>
            <div class="endpoint">
                <div class="method">GET</div>
                <code>/redoc</code> - Alternative API documentation
            </div>
            
            <h2>🔍 Main Endpoints</h2>
            <div class="endpoint">
                <div class="method">POST</div>
                <code>/calculate</code> - Single gear measurement calculation
            </div>
            <div class="endpoint">
                <div class="method">POST</div>
                <code>/batch</code> - Batch calculations (up to 50 gears)
            </div>
            <div class="endpoint">
                <div class="method">GET</div>
                <code>/health</code> - API health and feature status
            </div>
            
            <h2>✨ Features</h2>
            <div class="feature">Advanced helical gear corrections (0° to 45°)</div>
            <div class="feature">Both external (MOP) and internal (MBP) gears</div>
            <div class="feature">Multi-term correction formulas with range-specific coefficients</div>
            <div class="feature">Automatic pin diameter calculation</div>
            <div class="feature">Comprehensive validation and error handling</div>
            <div class="feature">Uncertainty estimation and quality assessment</div>
            <div class="feature">Support for both DP and metric units</div>
            <div class="feature">Professional-grade precision (microinch level)</div>
            
            <h2>📖 Example Usage</h2>
            <p>Try the <a href="/docs" style="color: #3498db; text-decoration: none;">interactive documentation</a> to test the API endpoints directly in your browser!</p>
        </div>
    </body>
    </html>
    """
    return html_content

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        features=[
            "Advanced helical corrections",
            "Multi-term correction formulas", 
            "Range-specific coefficients",
            "External and internal gears",
            "Batch processing",
            "Uncertainty estimation",
            "Quality assessment"
        ]
    )

@app.post("/calculate", response_model=GearCalculationResult)
async def calculate_gear_measurement(request: GearCalculationRequest):
    """
    Calculate measurement over pins (MOP) or measurement between pins (MBP)
    
    Supports:
    - External gears (MOP) and internal gears (MBP)
    - Spur gears (helix_angle = 0) and helical gears (helix_angle ≠ 0)
    - Automatic pin diameter calculation
    - Advanced helical corrections with multi-term formulas
    """
    try:
        # Auto-calculate pin diameter if requested
        pin_diameter = request.pin_diameter
        if request.use_best_pin or pin_diameter is None:
            dp_for_pin = request.diametral_pitch
            if request.is_metric:
                dp_for_pin = 25.4 / request.diametral_pitch  # Convert module to DP
            pin_diameter = best_pin_rule(dp_for_pin, request.pressure_angle)
        
        # Create gear parameters for the agent
        gear_params = GearParameters(
            teeth=request.teeth,
            diametral_pitch=request.diametral_pitch,
            pressure_angle=request.pressure_angle,
            tooth_thickness=request.tooth_thickness,
            pin_diameter=pin_diameter,
            helix_angle=request.helix_angle,
            is_internal=request.is_internal,
            is_metric=request.is_metric
        )
        
        # Use the gear metrology agent for calculation
        if gear_agent is None:
            raise HTTPException(status_code=500, detail="Gear metrology agent not initialized")
        
        calc_result = gear_agent.calculate_measurement_over_pins(gear_params)
        analysis = gear_agent.analyze_gear_configuration(gear_params)
        
        # Determine coefficient set used
        coefficient_set = None
        if abs(request.helix_angle) > 0.01:
            helix_abs = abs(request.helix_angle)
            if helix_abs <= 8.0:
                coefficient_set = "Low Helix (0-8°)"
            elif helix_abs <= 14.0:
                coefficient_set = "Medium Helix (8-14°)"
            elif helix_abs <= 25.0:
                coefficient_set = "High Helix (14-25°)"
            else:
                coefficient_set = "Very High Helix (25-45°)"
        
        # Build response
        return GearCalculationResult(
            measurement_value=calc_result.measurement_value,
            measurement_type=calc_result.measurement_type,
            method=calc_result.method,
            uncertainty=calc_result.uncertainty,
            input_parameters=request,
            pitch_diameter=calc_result.pitch_diameter,
            base_diameter=calc_result.base_diameter,
            contact_angle=calc_result.contact_angle,
            helical_correction=calc_result.helical_correction,
            coefficient_set=coefficient_set,
            quality_rating=analysis['quality_assessment'],
            calculation_notes=calc_result.calculation_notes
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid input parameters: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")

@app.post("/batch", response_model=BatchCalculationResult)
async def batch_calculate(request: BatchCalculationRequest):
    """
    Perform batch calculations for multiple gears
    
    Maximum 50 calculations per request for performance reasons.
    """
    if len(request.calculations) == 0:
        raise HTTPException(status_code=400, detail="No calculations provided")
    
    if len(request.calculations) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 calculations per batch")
    
    results = []
    errors = []
    
    for i, calc_request in enumerate(request.calculations):
        try:
            result = await calculate_gear_measurement(calc_request)
            results.append(result)
        except HTTPException as e:
            errors.append(f"Calculation {i+1}: {e.detail}")
        except Exception as e:
            errors.append(f"Calculation {i+1}: Unexpected error - {str(e)}")
    
    # Generate summary
    summary = {
        "total_requested": len(request.calculations),
        "successful": len(results),
        "failed": len(errors),
        "success_rate": len(results) / len(request.calculations) * 100,
        "errors": errors if errors else None
    }
    
    return BatchCalculationResult(
        results=results,
        summary=summary
    )

@app.get("/examples")
async def get_examples():
    """Get example API requests for testing"""
    return {
        "single_calculation": {
            "url": "/calculate",
            "method": "POST",
            "example_external_spur": {
                "teeth": 45,
                "diametral_pitch": 8.0,
                "pressure_angle": 20.0,
                "tooth_thickness": 0.1963,
                "pin_diameter": 0.210,
                "helix_angle": 0.0,
                "is_internal": False,
                "is_metric": False,
                "use_best_pin": False
            },
            "example_external_helical": {
                "teeth": 127,
                "diametral_pitch": 12.0,
                "pressure_angle": 20.0,
                "tooth_thickness": 0.130900,
                "helix_angle": 15.0,
                "is_internal": False,
                "is_metric": False,
                "use_best_pin": True
            },
            "example_internal_helical": {
                "teeth": 80,
                "diametral_pitch": 10.0,
                "pressure_angle": 20.0,
                "tooth_thickness": 0.1571,
                "helix_angle": 10.5,
                "is_internal": True,
                "is_metric": False,
                "use_best_pin": True
            }
        },
        "batch_calculation": {
            "url": "/batch",
            "method": "POST",
            "example": {
                "calculations": [
                    {
                        "teeth": 45,
                        "diametral_pitch": 8.0,
                        "pressure_angle": 20.0,
                        "tooth_thickness": 0.1963,
                        "helix_angle": 0.0,
                        "is_internal": False,
                        "use_best_pin": True
                    },
                    {
                        "teeth": 127,
                        "diametral_pitch": 12.0,
                        "pressure_angle": 20.0,
                        "tooth_thickness": 0.130900,
                        "helix_angle": 15.0,
                        "is_internal": False,
                        "use_best_pin": True
                    }
                ]
            }
        }
    }

@app.get("/stats")
async def get_calculation_stats():
    """Get calculation statistics"""
    if gear_agent is None:
        raise HTTPException(status_code=500, detail="Gear metrology agent not initialized")
    
    history = gear_agent.get_calculation_history()
    
    if not history:
        return {"message": "No calculations performed yet"}
    
    # Analyze calculation history
    total_calcs = len(history)
    external_count = sum(1 for h in history if h.measurement_type == "MOP")
    internal_count = sum(1 for h in history if h.measurement_type == "MBP")
    helical_count = sum(1 for h in history if abs(h.gear_parameters.helix_angle) > 0.01)
    
    return {
        "total_calculations": total_calcs,
        "external_gears": external_count,
        "internal_gears": internal_count,
        "helical_gears": helical_count,
        "spur_gears": total_calcs - helical_count,
        "average_uncertainty": sum(h.uncertainty for h in history) / total_calcs if total_calcs > 0 else 0
    }

# Development server runner
def main():
    """Run the development server"""
    print("🚀 Starting Gear Metrology API...")
    print("📖 API Documentation: http://localhost:8000/docs")
    print("🔍 Alternative Docs: http://localhost:8000/redoc")
    print("🏠 Home Page: http://localhost:8000/")
    
    uvicorn.run(
        "gear_api:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()