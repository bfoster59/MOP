#!/usr/bin/env python3
"""
Secure FastAPI Implementation for MOP Gear Metrology System
Enhanced with authentication, rate limiting, and comprehensive validation
"""

import os
import time
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from collections import defaultdict
import json

try:
    from fastapi import FastAPI, HTTPException, Depends, Request, status
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel, Field, validator
    import uvicorn
except ImportError:
    print("FastAPI dependencies not installed. Install with: pip install fastapi uvicorn pydantic")
    exit(1)

# Import our modules
try:
    from MOP import mow_spur_external_dp, mbp_spur_internal_dp, mow_helical_external_dp, mbp_helical_internal_dp
    from validation import InputValidator, GearValidationError, ValidationResult
except ImportError as e:
    print(f"Error importing modules: {e}")
    exit(1)

# Security configuration
SECURITY_CONFIG = {
    'api_key_length': 32,
    'rate_limit_requests': 100,  # requests per window
    'rate_limit_window': 3600,   # window in seconds (1 hour)
    'max_batch_size': 50,        # maximum gears per batch
    'session_timeout': 86400,    # 24 hours
}

# In-memory storage (use database in production)
api_keys = {}
rate_limit_store = defaultdict(list)
session_store = {}

class RateLimiter:
    """Simple in-memory rate limiter"""
    
    @staticmethod
    def is_allowed(client_id: str, limit: int = SECURITY_CONFIG['rate_limit_requests'], 
                   window: int = SECURITY_CONFIG['rate_limit_window']) -> bool:
        """Check if client is within rate limits"""
        current_time = time.time()
        
        # Clean old entries
        rate_limit_store[client_id] = [
            timestamp for timestamp in rate_limit_store[client_id]
            if current_time - timestamp < window
        ]
        
        # Check if under limit
        if len(rate_limit_store[client_id]) >= limit:
            return False
        
        # Add current request
        rate_limit_store[client_id].append(current_time)
        return True
    
    @staticmethod
    def get_remaining(client_id: str, limit: int = SECURITY_CONFIG['rate_limit_requests']) -> int:
        """Get remaining requests for client"""
        current_count = len(rate_limit_store[client_id])
        return max(0, limit - current_count)

class APIKeyManager:
    """Manage API keys and authentication"""
    
    @staticmethod
    def generate_api_key() -> str:
        """Generate a secure API key"""
        return secrets.token_urlsafe(SECURITY_CONFIG['api_key_length'])
    
    @staticmethod
    def hash_key(api_key: str) -> str:
        """Hash API key for storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    @staticmethod
    def create_user(username: str, permissions: List[str] = None) -> str:
        """Create a new user and return API key"""
        if permissions is None:
            permissions = ['calculate', 'batch']
        
        api_key = APIKeyManager.generate_api_key()
        key_hash = APIKeyManager.hash_key(api_key)
        
        api_keys[key_hash] = {
            'username': username,
            'permissions': permissions,
            'created': datetime.utcnow().isoformat(),
            'last_used': None,
            'request_count': 0
        }
        
        return api_key
    
    @staticmethod
    def validate_key(api_key: str) -> Optional[Dict[str, Any]]:
        """Validate API key and return user info"""
        key_hash = APIKeyManager.hash_key(api_key)
        user_info = api_keys.get(key_hash)
        
        if user_info:
            # Update last used timestamp
            user_info['last_used'] = datetime.utcnow().isoformat()
            user_info['request_count'] += 1
        
        return user_info

# Pydantic models with enhanced validation
class GearRequest(BaseModel):
    """Request model for gear calculations with comprehensive validation"""
    
    z: int = Field(..., description="Number of teeth", ge=4, le=1000)
    dp: float = Field(..., description="Diametral pitch (1/inch) or Module (mm)", gt=0, le=1000)
    pa: float = Field(..., description="Pressure angle (degrees)", ge=5, le=45)
    helix: float = Field(0.0, description="Helix angle (degrees)", ge=-45, le=45)
    t: Optional[float] = Field(None, description="Tooth thickness (external) or space width (internal)", gt=0, le=100)
    s: Optional[float] = Field(None, description="Space width for internal gears", gt=0, le=100)
    d: Optional[float] = Field(None, description="Pin diameter", gt=0, le=50)
    gear_type: str = Field(..., description="Gear type: 'external' or 'internal'")
    use_best_pin: bool = Field(False, description="Use best pin diameter calculation")
    unit_system: str = Field("standard", description="Unit system: 'standard' (DP) or 'module'")
    
    @validator('gear_type')
    def validate_gear_type(cls, v):
        if v not in ['external', 'internal']:
            raise ValueError("gear_type must be 'external' or 'internal'")
        return v
    
    @validator('unit_system')
    def validate_unit_system(cls, v):
        if v not in ['standard', 'module']:
            raise ValueError("unit_system must be 'standard' or 'module'")
        return v

class BatchRequest(BaseModel):
    """Request model for batch calculations"""
    
    gears: List[GearRequest] = Field(..., description="List of gear calculations")
    
    @validator('gears')
    def validate_batch_size(cls, v):
        if len(v) > SECURITY_CONFIG['max_batch_size']:
            raise ValueError(f"Batch size {len(v)} exceeds maximum {SECURITY_CONFIG['max_batch_size']}")
        return v

class GearResponse(BaseModel):
    """Response model for gear calculations"""
    
    success: bool
    mop: Optional[float] = None
    method: Optional[str] = None
    pitch_diameter: Optional[float] = None
    base_diameter: Optional[float] = None
    contact_angle: Optional[float] = None
    uncertainty: Optional[float] = None
    warnings: List[str] = []
    calculation_time: Optional[float] = None

class ErrorResponse(BaseModel):
    """Error response model"""
    
    success: bool = False
    error: str
    error_code: str
    timestamp: str

# FastAPI app initialization
app = FastAPI(
    title="MOP Gear Metrology API",
    description="Secure API for high-precision gear measurement calculations",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware with restrictions
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],  # Restrict to known origins
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Security setup
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency to validate API key"""
    
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_info = APIKeyManager.validate_key(credentials.credentials)
    
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user_info

async def check_rate_limit(request: Request, user_info: dict = Depends(get_current_user)):
    """Dependency to check rate limits"""
    
    client_id = f"{user_info['username']}:{request.client.host}"
    
    if not RateLimiter.is_allowed(client_id):
        remaining = RateLimiter.get_remaining(client_id)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. {remaining} requests remaining.",
            headers={
                "X-RateLimit-Limit": str(SECURITY_CONFIG['rate_limit_requests']),
                "X-RateLimit-Remaining": str(remaining),
                "X-RateLimit-Reset": str(int(time.time() + SECURITY_CONFIG['rate_limit_window']))
            }
        )
    
    return user_info

def safe_calculate_gear(gear_request: GearRequest) -> GearResponse:
    """Safely calculate gear measurements with comprehensive validation"""
    
    start_time = time.time()
    warnings = []
    
    try:
        # Input validation
        if gear_request.gear_type == "external":
            if gear_request.t is None:
                if not gear_request.use_best_pin:
                    raise GearValidationError("Tooth thickness 't' required for external gears")
            
            validation_result = InputValidator.validate_complete_external_gear(
                z=gear_request.z,
                dp=gear_request.dp,
                pa=gear_request.pa,
                t=gear_request.t or 0.0,  # Will be calculated if use_best_pin
                d=gear_request.d or 0.0,  # Will be calculated if use_best_pin
                helix=gear_request.helix
            )
        else:  # internal
            if gear_request.s is None:
                raise GearValidationError("Space width 's' required for internal gears")
            
            validation_result = InputValidator.validate_complete_internal_gear(
                z=gear_request.z,
                dp=gear_request.dp,
                pa=gear_request.pa,
                s=gear_request.s,
                d=gear_request.d or 0.0,  # Will be calculated if use_best_pin
                helix=gear_request.helix
            )
        
        if not validation_result.is_valid:
            raise GearValidationError(f"Validation failed: {'; '.join(validation_result.errors)}")
        
        warnings.extend(validation_result.warnings)
        
        # Unit conversion if needed
        dp = gear_request.dp
        if gear_request.unit_system == "module":
            dp = 25.4 / gear_request.dp  # Convert module to DP
        
        # Calculate pin diameter if needed
        d = gear_request.d
        if gear_request.use_best_pin or d is None:
            from MOP import best_pin_rule
            d = best_pin_rule(dp, gear_request.pa)
        
        # Calculate tooth thickness for external gears if needed
        t = gear_request.t
        if gear_request.gear_type == "external" and (t is None or gear_request.use_best_pin):
            import math
            t = math.pi / (2.0 * dp)  # Standard tooth thickness
        
        # Perform calculation
        if gear_request.gear_type == "external":
            if abs(gear_request.helix) > 0.01:
                result = mow_helical_external_dp(
                    z=gear_request.z, normal_DP=dp, normal_alpha_deg=gear_request.pa,
                    t=t, d=d, helix_deg=gear_request.helix
                )
            else:
                result = mow_spur_external_dp(
                    z=gear_request.z, DP=dp, alpha_deg=gear_request.pa,
                    t=t, d=d
                )
        else:  # internal
            if abs(gear_request.helix) > 0.01:
                result = mbp_helical_internal_dp(
                    z=gear_request.z, normal_DP=dp, normal_alpha_deg=gear_request.pa,
                    s=gear_request.s, d=d, helix_deg=gear_request.helix
                )
            else:
                result = mbp_spur_internal_dp(
                    z=gear_request.z, DP=dp, alpha_deg=gear_request.pa,
                    s=gear_request.s, d=d
                )
        
        # Calculate uncertainty estimate
        base_uncertainty = 0.00003  # Base uncertainty in inches
        helix_factor = abs(gear_request.helix) * 0.000001  # Additional uncertainty for helical
        uncertainty = base_uncertainty + helix_factor
        
        calculation_time = time.time() - start_time
        
        return GearResponse(
            success=True,
            mop=result.MOW,
            method=result.method,
            pitch_diameter=result.Dp,
            base_diameter=result.Db,
            contact_angle=result.beta_deg,
            uncertainty=uncertainty,
            warnings=warnings,
            calculation_time=calculation_time
        )
        
    except GearValidationError as e:
        return GearResponse(
            success=False,
            warnings=[str(e)]
        )
    except Exception as e:
        # Log error in production
        return GearResponse(
            success=False,
            warnings=[f"Calculation error: {str(e)}"]
        )

# API Endpoints

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "MOP Gear Metrology API",
        "version": "2.0.0",
        "description": "Secure API for high-precision gear measurement calculations",
        "documentation": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0",
        "rate_limits": {
            "requests_per_hour": SECURITY_CONFIG['rate_limit_requests'],
            "max_batch_size": SECURITY_CONFIG['max_batch_size']
        }
    }

@app.post("/calculate", response_model=GearResponse)
async def calculate_gear(
    gear_request: GearRequest,
    user_info: dict = Depends(check_rate_limit)
):
    """Calculate gear measurement with authentication and rate limiting"""
    
    # Check permissions
    if 'calculate' not in user_info.get('permissions', []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions for calculation"
        )
    
    return safe_calculate_gear(gear_request)

@app.post("/batch")
async def batch_calculate(
    batch_request: BatchRequest,
    user_info: dict = Depends(check_rate_limit)
):
    """Batch calculation with authentication and rate limiting"""
    
    # Check permissions
    if 'batch' not in user_info.get('permissions', []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions for batch calculation"
        )
    
    results = []
    
    for gear_request in batch_request.gears:
        result = safe_calculate_gear(gear_request)
        results.append(result)
    
    return {
        "success": True,
        "results": results,
        "count": len(results),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/auth/create-key")
async def create_api_key(username: str, admin_key: str):
    """Create new API key (admin only)"""
    
    # Simple admin authentication (use proper auth in production)
    if admin_key != os.getenv("ADMIN_KEY", "admin123"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin key"
        )
    
    api_key = APIKeyManager.create_user(username)
    
    return {
        "success": True,
        "username": username,
        "api_key": api_key,
        "note": "Store this key securely. It cannot be retrieved again."
    }

@app.get("/auth/info")
async def get_user_info(user_info: dict = Depends(get_current_user)):
    """Get current user information"""
    
    # Remove sensitive information
    safe_info = {
        "username": user_info['username'],
        "permissions": user_info['permissions'],
        "request_count": user_info['request_count'],
        "last_used": user_info['last_used']
    }
    
    return safe_info

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler"""
    
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            error_code=f"HTTP_{exc.status_code}",
            timestamp=datetime.utcnow().isoformat()
        ).dict()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """General exception handler"""
    
    # Log error in production
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            error_code="INTERNAL_ERROR",
            timestamp=datetime.utcnow().isoformat()
        ).dict()
    )

# Initialize with demo API key
if __name__ == "__main__":
    # Create demo API key
    demo_key = APIKeyManager.create_user("demo_user", ["calculate", "batch"])
    print(f"Demo API Key: {demo_key}")
    print("Use this key in the Authorization header: Bearer {key}")
    print("\nStarting secure API server...")
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info"
    )