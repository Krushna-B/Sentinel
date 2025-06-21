from pydantic import BaseModel
from datetime import datetime

'''Allows Control on how data moves in and out of API'''
'''Validation and Security'''

class StateVector(BaseModel):
    timestamp: datetime
    x: float
    y: float
    z: float
    vx: float
    vy: float
    vz: float


class CreateStateVector(BaseModel):
    timestamp: datetime
    id: int
    x: float
    y: float
    z: float
    vx: float
    vy: float
    vz: float

class Config:
    orm_mode = True 