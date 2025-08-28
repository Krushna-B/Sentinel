from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Text, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from .database import Base



class Objects(Base):
    __tablename__ = "satellites"
    norad_id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    cospar_id  = Column(String)          
    object_type = Column(String)         
    country_code = Column(String(3))     
    launch_date  = Column(DateTime)        
    decay_date   = Column(DateTime)        
    rcs_size     = Column(String)       

    tle_sets = relationship("TleSet",back_populates="obj",cascade="all,delete-orphan")
    state_vectors = relationship("StateVector",back_populates="obj",cascade="all,delete-orphan")

class TleSet(Base):
    __tablename__ = "tle_sets"

    id        = Column(Integer, primary_key=True, autoincrement=True)
    norad_id  = Column(Integer, ForeignKey("satellites.norad_id", ondelete="CASCADE"), index=True)
    epoch     = Column(DateTime(timezone=True), index=True) 

    line1 = Column(Text, nullable=False)  
    line2 = Column(Text, nullable=False)  

    
    bstar           = Column(Float)   
    element_set_no  = Column(Integer)  

   
    mean_motion       = Column(Float)   
    eccentricity      = Column(Float)  
    inclination       = Column(Float)   
    ra_of_asc_node    = Column(Float)   
    arg_of_pericenter = Column(Float)   
    mean_anomaly      = Column(Float)   
    mm_dot            = Column(Float)   
    mm_ddot           = Column(Float)   
    classification_type = Column(String)  
    ephemeris_type    = Column(Integer)    
    rev_at_epoch      = Column(Integer) 

    obj = relationship("Objects",back_populates="tle_sets") 

    __table_args__ = (
        UniqueConstraint("norad_id","epoch",name="uq_tle_norad_epoch"),
        Index("ix_tle_norad_epoch","norad_id","epoch")
    )



class StateVector(Base):
    __tablename__ = "state_vectors"
    id = Column(Integer,primary_key=True, index=True)  
    timestamp = Column(DateTime(timezone=True), index=True)
    norad_id = Column(Integer, ForeignKey("satellites.norad_id", ondelete="CASCADE"), index=True)
    x = Column(Float)
    y = Column(Float)
    z = Column(Float)
    vx = Column(Float)
    vy = Column(Float)
    vz = Column(Float)

    
    obj = relationship("Objects", back_populates="state_vectors")

    __table_args__ = (
        UniqueConstraint("norad_id", "timestamp", name="uq_sv_norad_ts"),
        Index("ix_sv_norad_ts", "norad_id", "timestamp"),
    )

    