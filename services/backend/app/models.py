from sqlalchemy import Column, Integer, Float, DateTime
from .database import Base


class StateVector(Base):
    __tablename__ = "state_vectors"
    id = Column(Integer,primary_key=True, index=True)  
    timestamp = Column(DateTime, index = True)
    norad_id = Column(Integer, index=True)  
    x = Column(Float)
    y = Column(Float)
    z = Column(Float)
    vx = Column(Float)
    vy = Column(Float)
    vz = Column(Float)
