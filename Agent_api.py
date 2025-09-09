from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Literal, Optional
from MOP import (
    mow_spur_external_dp, mbp_spur_internal_dp,
    mow_helical_external_dp, mbp_helical_internal_dp,
    best_pin_rule
)

app = FastAPI(title="Gear Expert API (MOP)")

class MeasureReq(BaseModel):
    kind: Literal["gear","spline"] = "gear"        # label only
    mode: Literal["external","internal"] = "external"
    z: int
    dp: float
    pa: float = Field(..., description="pressure angle (deg)")
    t: float = Field(..., description="tooth thickness (external) or space width (internal)")
    d: Optional[float] = Field(None, description="pin dia; omit to auto-pick")
    helix: float = 0.0
    best_pin: bool = False           # if True and d is omitted, use rule-of-thumb

class MeasureRes(BaseModel):
    method: Literal["2-wire","3-wire","2-pin","odd tooth"]
    measurement: float
    label: Literal["MOP","MBP"]
    derived: dict

@app.post("/measurements", response_model=MeasureRes)
def measurements(req: MeasureReq):
    d = req.d
    if d is None and req.best_pin:
        d = best_pin_rule(req.dp, req.pa)
    if d is None:
        raise HTTPException(400, "Pin diameter d required unless best_pin=True")

    helix = float(req.helix or 0.0)
    is_helical = abs(helix) > 1e-2

    if req.mode == "internal":
        if is_helical:
            r = mbp_helical_internal_dp(req.z, req.dp, req.pa, req.t, d, helix)
        else:
            r = mbp_spur_internal_dp(req.z, req.dp, req.pa, req.t, d)
        label = "MBP"
    else:
        if is_helical:
            r = mow_helical_external_dp(req.z, req.dp, req.pa, req.t, d, helix)
        else:
            r = mow_spur_external_dp(req.z, req.dp, req.pa, req.t, d)
        label = "MOP"

    # Normalize naming (“2-wire/3-wire” vs “2-pin/odd tooth”)
    method = "3-wire" if (req.z % 2) else "2-wire"

    return MeasureRes(
        method=method if not is_helical else r.method,   # keep your helical label if you prefer
        measurement=round(r.MOW, 4),
        label=label,
        derived={
            "Dp": r.Dp, "Db": r.Db, "beta_deg": r.beta_deg,
            "C2": r.C2, "odd_factor": (req.z % 2 == 1),
            "wire": d, "helix": helix
        }
    )
