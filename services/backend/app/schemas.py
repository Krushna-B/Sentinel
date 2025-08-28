from pydantic import BaseModel
from datetime import datetime
from typing import List, Tuple
from pydantic import BaseModel, Field, ConfigDict

'''Allows Control on how data moves in and out of API'''
'''Validation and Security'''

class StateVector(BaseModel):
    timestamp: datetime
    norad_id: int
    x: float
    y: float
    z: float
    vx: float
    vy: float
    vz: float


class CreateStateVector(BaseModel):
    timestamp: datetime
    norad_id: int
    x: float
    y: float
    z: float
    vx: float
    vy: float
    vz: float


class SatOrbit(BaseModel):
    norad_id: int
    lat: float  = Field(..., description="Latitude (deg)")
    lon: float  = Field(..., description="Longitude (deg)")
    alt: float  = Field(..., description="Altitude above MSL (km)")
    path: List[Tuple[float, float, float]] = Field(
        default_factory=list,
        description="Orbit samples as (lat, lon, alt_km)",
    )

class TLEOut(BaseModel):
    norad_id: int
    epoch: datetime | None = None
    line1: str
    line2: str



class Config:
    orm_mode = True 