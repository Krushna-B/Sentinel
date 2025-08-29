
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from math import cos, sin, sqrt, asin, atan2, degrees, pi
from typing import List, Tuple, Sequence, cast

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from ..database import get_db

# ---- Alias ORM models (avoid name clashes) ----
from ..models import Objects as ObjectsModel
from ..models import StateVector as StateVectorModel
from ..models import TleSet as TleSetModel

# ---- Import schemas for response_model typing ----
from ..schemas import StateVector as StateVectorSchema
from ..schemas import TLEOut as TLEOutSchema
from ..schemas import SatOrbit as SatOrbitSchema
from ..schemas import SatPointOut 

from sgp4.api import Satrec, jday

router = APIRouter(prefix="/api")
R_EARTH_KM = 6371.0




def _gmst_rad(ts: datetime) -> float:
    jd, fr = jday(ts.year, ts.month, ts.day,
                  ts.hour, ts.minute, ts.second + ts.microsecond * 1e-6)
    T = ((jd + fr) - 2451545.0) / 36525.0
    gmst_sec = 67310.54841 + (876600.0 * 3600 + 8640184.812866) * T + 0.093104 * (T**2) - 6.2e-6 * (T**3)
    gmst_sec %= 86400.0
    if gmst_sec < 0:
        gmst_sec += 86400.0
    return (gmst_sec * 2.0 * pi) / 86400.0

def eci_to_geodetic_spherical(x: float, y: float, z: float, ts: datetime) -> Tuple[float, float, float]:
    """Fast ECI→(lat, lon, alt_km) for visualization."""
    theta = _gmst_rad(ts)
    ct, st = cos(theta), sin(theta)
    x_e = ct * x + st * y
    y_e = -st * x + ct * y
    z_e = z
    r_xy = sqrt(x_e*x_e + y_e*y_e)
    r = sqrt(r_xy*r_xy + z_e*z_e)
    lat = degrees(asin(z_e / r)) if r else 0.0
    lon = degrees(atan2(y_e, x_e))
    if lon > 180: lon -= 360
    if lon < -180: lon += 360
    alt_km = r - R_EARTH_KM
    return lat, lon, alt_km

def _period_minutes_from_line2(line2: str) -> float | None:
    try:
        rev_per_day = float(line2[52:63])  #
        return 1440.0 / rev_per_day
    except Exception:
        return None




@router.get("/state-vectors/latest", response_model=List[StateVectorSchema])
def latest_state_vectors(
    limit: int = Query(10000, ge=1, le=30000),
    db: Session = Depends(get_db),
):
    """
    Latest ECI state vector per satellite.
    Returns fields matching your `StateVector` schema.
    """
    subq = (
        select(StateVectorModel.norad_id, func.max(StateVectorModel.timestamp).label("ts"))
        .group_by(StateVectorModel.norad_id)
        .subquery()
    )

    stmt = (
        select(StateVectorModel)
        .join(subq, (StateVectorModel.norad_id == subq.c.norad_id) &
                   (StateVectorModel.timestamp == subq.c.ts))
        .order_by(StateVectorModel.norad_id)
        .limit(limit)
    )

    rows: Sequence[StateVectorModel] = db.execute(stmt).scalars().all()

   
    return [
        {
            "timestamp": r.timestamp,
            "norad_id": r.norad_id,
            "x": r.x, "y": r.y, "z": r.z,
            "vx": r.vx, "vy": r.vy, "vz": r.vz,
        }
        for r in rows
    ]


@router.get("/satellites/{norad_id}")
def satellite_details(norad_id: int, db: Session = Depends(get_db)):
    """Satellite metadata for hover card."""
    s = db.get(ObjectsModel, norad_id)
    if not s:
        raise HTTPException(404, "Satellite not found")
    return {
        "norad_id": s.norad_id,
        "name": s.name,
        "cospar_id": s.cospar_id,
        "object_type": s.object_type,
        "country_code": s.country_code,
        "launch_date": s.launch_date,
        "decay_date": s.decay_date,
        "rcs_size": s.rcs_size,
    }


@router.get("/satellites/{norad_id}/tle/latest", response_model=TLEOutSchema)
def tle_latest(norad_id: int, db: Session = Depends(get_db)):
    """Latest TLE lines for a satellite (for orbit path on hover)."""
    stmt = (
        select(TleSetModel)
        .where(TleSetModel.norad_id == norad_id)
        .order_by(TleSetModel.epoch.desc())
        .limit(1)
    )
    tle = db.execute(stmt).scalars().first()
    if not tle:
        raise HTTPException(404, "No TLE found")
    
    return {
        "norad_id": tle.norad_id,
        "epoch": tle.epoch,
        "line1": tle.line1,
        "line2": tle.line2,
    }


@router.get("/satellites/{norad_id}/orbit", response_model=SatOrbitSchema)
def orbit_samples(
    norad_id: int,
    periods: int = Query(1, ge=1, le=3),
    samples: int = Query(180, ge=60, le=720),
    db: Session = Depends(get_db),
):
    """
    Returns orbit samples (lat, lon, alt_km) over `periods` orbital periods.
    Uses latest TLE and SGP4; path length = `samples` points.
    """
    stmt = (
        select(TleSetModel)
        .where(TleSetModel.norad_id == norad_id)
        .order_by(TleSetModel.epoch.desc())
        .limit(1)
    )
    tle = db.execute(stmt).scalars().first()
    if not tle:
        raise HTTPException(404, "No TLE found")
    
    line2_text = str(tle.line2)              # <-- coerce for the type checker
    period_min = _period_minutes_from_line2(line2_text) or 90.0

    rec = Satrec.twoline2rv(tle.line1, tle.line2)
    period_min = _period_minutes_from_line2(line2_text) or 90.0
    total_min = period_min * periods
    dt_sec = (total_min * 60.0) / samples

    start = datetime.now(timezone.utc)
    path: List[Tuple[float, float, float]] = []

    for i in range(samples + 1):
        t = start + timedelta(seconds=i * dt_sec)
        jd, fr = jday(t.year, t.month, t.day, t.hour, t.minute, t.second + t.microsecond * 1e-6)
        e, r, _ = rec.sgp4(jd, fr)
        if e != 0 or r is None:
            continue
        lat, lon, alt_km = eci_to_geodetic_spherical(r[0], r[1], r[2], t)
        path.append((lat, lon, alt_km))

    lat0, lon0, alt0 = path[0] if path else (0.0, 0.0, 0.0)
    return {
        "norad_id": norad_id,
        "lat": lat0,
        "lon": lon0,
        "alt": alt0,
        "path": path,
    }

@router.get("/satellites/positions/all", response_model=List[SatPointOut])
def all_satellite_positions(
    db: Session = Depends(get_db),
):
    """
    Current position (lat, lon, alt_km) for every satellite, using the latest TLE only.
    Computes everyone at the same UTC timestamp (now).
    """
    # Latest TLE per NORAD
    latest_subq = (
        select(
            TleSetModel.norad_id.label("norad_id"),
            func.max(TleSetModel.epoch).label("max_epoch"),
        )
        .group_by(TleSetModel.norad_id)
        .subquery()
    )

    stmt = (
        select(TleSetModel)
        .join(
            latest_subq,
            (TleSetModel.norad_id == latest_subq.c.norad_id)
            & (TleSetModel.epoch == latest_subq.c.max_epoch),
        )
        .order_by(TleSetModel.norad_id)
    )

  
    rows: Sequence[TleSetModel] = db.execute(stmt).scalars().all()
   

    t_now = datetime.now(timezone.utc)
    jd, fr = jday(
        t_now.year, t_now.month, t_now.day,
        t_now.hour, t_now.minute, t_now.second + t_now.microsecond * 1e-6
    )

    out: List[SatPointOut] = []
    for tle in rows:
        try:
            
            line1 = cast(str, tle.line1)
            line2 = cast(str, tle.line2)
            norad = cast(int, tle.norad_id)

            rec = Satrec.twoline2rv(line1, line2)
            e, r, _ = rec.sgp4(jd, fr)
            if e != 0 or r is None:
                continue

            lat, lon, alt_km = eci_to_geodetic_spherical(r[0], r[1], r[2], t_now)
            out.append(SatPointOut(norad_id=norad, lat=float(lat), lon=float(lon), alt=float(alt_km)))
        except Exception:
            continue

    return out