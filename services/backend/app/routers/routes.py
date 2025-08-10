from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from .. import database, models, schemas
from ..utils.orbit import state_to_elements, elements_to_r, eci_to_lla, MU
import math, numpy as np

router = APIRouter()

@router.get("/satillites", response_model=list[schemas.SatOrbit])
def orbits_from_state(
    limit: int = Query(100, gt=1, le=10000),
    step: int = Query(60, ge=10, le=600),
    db: Session = Depends(database.get_db),
):
   
    subq = (
        db.query(models.StateVector)
          .distinct(models.StateVector.norad_id)
          .order_by(models.StateVector.norad_id,
                    models.StateVector.timestamp.desc())
          .limit(limit*2)
          .subquery()
    )
    rows = db.query(subq).limit(limit).all()
    if not rows:
        raise HTTPException(404, "No data")

    out: list[schemas.SatOrbit] = []
    for r in rows:
        a,e,i,RAAN,ω,M0 = state_to_elements(
            (r.x,r.y,r.z), (r.vx,r.vy,r.vz)
        )
        period = 2*math.pi*math.sqrt(a**3 / MU)
        samples = int(period // step) + 1

        path=[]
        for k in range(samples):
            M = (M0 + 2*math.pi*(k*step)/period) % (2*math.pi)
            r_eci = elements_to_r(a,e,i,RAAN,ω,M)
            lat,lon,alt = eci_to_lla(np.asarray(r_eci))
            path.append((lat,lon,alt))

        out.append(schemas.SatOrbit(
            norad_id=r.norad_id,
            lat=path[0][0],
            lon=path[0][1],
            alt=path[0][2],
            path=path,
          
        ))
    return out
