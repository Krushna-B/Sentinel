from pydantic import BaseModel
from datetime import datetime
from typing import List, Tuple

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
    lat: float
    lon: float
    alt: float
    path: List[Tuple[float, float,float]] 
class Config:
    orm_mode = True 