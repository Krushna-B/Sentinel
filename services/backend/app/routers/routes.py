
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from math import cos, sin, sqrt, asin, atan2, degrees, pi
from typing import List, Tuple, Sequence, Dict, Optional, cast, Literal

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

from sgp4.api import Satrec, jday

from sgp4.ext import invjday 

router = APIRouter(prefix="/api")
R_EARTH_KM = 6371.0


# ---------- helpers ----------

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
        rev_per_day = float(line2[52:63])  # cols 53–63
        return 1440.0 / rev_per_day
    except Exception:
        return None

def _tle_epoch_from_line1(line1: str) -> Optional[datetime]:
    """
    Parse TLE epoch from line 1:
      cols 19–20 = year (YY), cols 21–32 = day-of-year with fraction.
    Returns tz-aware (UTC) datetime, or None if parsing fails.
    """
    try:
        yy = int(line1[18:20])          # 19–20
        doy = float(line1[20:32])       # 21–32
        year = 2000 + yy if yy < 57 else 1900 + yy  # NORAD cutoff
        day_int = int(doy)
        sec = (doy - day_int) * 86400.0
        base = datetime(year, 1, 1, tzinfo=timezone.utc)
        return base + timedelta(days=day_int - 1, seconds=sec)
    except Exception:
        return None
# ---------- endpoints ----------



def _latest_tles_for_ids(db: Session, ids: list[int]) -> Dict[int, TleSetModel]:
    # Prefer non-NULL epochs as "latest"
    rows = (
        db.query(TleSetModel)
          .filter(TleSetModel.norad_id.in_(ids))
          .order_by(
              TleSetModel.norad_id.asc(),
              TleSetModel.epoch.desc().nullslast()
          )
          .all()
    )
    latest: Dict[int, TleSetModel] = {}
    for row in rows:
        nid = cast(int, row.norad_id)
        if nid not in latest:
            latest[nid] = row
    return latest

def eci_to_geodetic_with_theta(x: float, y: float, z: float, theta: float) -> Tuple[float, float, float]:
    """ECI -> (lat, lon, alt_km) using a FIXED Earth rotation angle `theta` (for ring-style paths)."""
    ct, st = cos(theta), sin(theta)
    x_e = ct * x + st * y
    y_e = -st * x + ct * y
    z_e = z
    r_xy = sqrt(x_e*x_e + y_e*y_e)
    r = sqrt(r_xy*r_xy + z_e*z_e)
    lat = degrees(atan2(z_e, r_xy))
    lon = degrees(atan2(y_e, x_e))
    if lon > 180: lon -= 360
    if lon < -180: lon += 360
    alt_km = r - R_EARTH_KM
    return lat, lon, alt_km


@router.get("/satellites/orbits")
def multi_orbits(
    ids: str = Query(..., description="Comma-separated NORAD IDs, e.g., 5,25544,20580"),
    at: Optional[datetime] = Query(None, description="UTC time (ISO-8601). Default: server NOW"),
    periods: int = Query(1, ge=1, le=3),
    samples: int = Query(0, ge=0, le=720),   # 0 = don't return path (just 'now')
    mode: Literal["track", "ring"] = Query("ring", description="'track' = ground track, 'ring' = fixed-orientation ring"),
    db: Session = Depends(get_db),
):
    """
    For each NORAD id, compute 'now' lat/lon/alt (km) from the latest TLE.
    Optionally include a forward path (lat,lon,alt) over `periods` periods with `samples` points.

    - mode='track' : path follows Earth rotation (ground track). [existing behavior]
    - mode='ring'  : path uses a fixed Earth orientation at t0 (pretty orbital ring).
    """
    try:
        id_list = [int(s) for s in ids.split(",") if s.strip()]
    except ValueError:
        raise HTTPException(400, "Invalid ids parameter")

    if not id_list:
        raise HTTPException(400, "No ids provided")
    if len(id_list) > 1000:
        raise HTTPException(413, "Too many ids (max 1000)")

    t0 = (at.astimezone(timezone.utc) if at else datetime.now(timezone.utc))
    latest = _latest_tles_for_ids(db, id_list)

    # Freeze Earth orientation for ring mode (use same GMST for all samples)
    theta0 = _gmst_rad(t0)

    results = []
    for nid in id_list:
        tle = latest.get(nid)
        if not tle:
            results.append({"norad_id": nid, "error": "No TLE found"})
            continue

        line1_text: str = cast(str, tle.line1)
        line2_text: str = cast(str, tle.line2)

        rec = Satrec.twoline2rv(line1_text, line2_text)
        period_min = _period_minutes_from_line2(line2_text) or 90.0

        jd0, fr0 = jday(
            t0.year, t0.month, t0.day,
            t0.hour, t0.minute, t0.second + t0.microsecond * 1e-6
        )
        e0, r0, v0 = rec.sgp4(jd0, fr0)
        if e0 != 0 or r0 is None:
            results.append({"norad_id": nid, "error": f"SGP4 error {e0}"})
            continue

        # Dot (current position) always uses true-now Earth rotation (unchanged)
        lat0, lon0, alt0 = eci_to_geodetic_spherical(r0[0], r0[1], r0[2], t0)

        path: List[Tuple[float, float, float]] = []
        dt_sec = 0.0
        if samples > 0:
            total_min = period_min * periods
            dt_sec = (total_min * 60.0) / samples
            for i in range(samples + 1):
                t = t0 + timedelta(seconds=i * dt_sec)
                jd, fr = jday(
                    t.year, t.month, t.day,
                    t.hour, t.minute, t.second + t.microsecond * 1e-6
                )
                e, r, _ = rec.sgp4(jd, fr)
                if e != 0 or r is None:
                    continue

                if mode == "ring":
                    # Fixed Earth orientation -> nice elliptical ring
                    lat, lon, alt_km = eci_to_geodetic_with_theta(r[0], r[1], r[2], theta0)
                else:
                    # Ground track (existing)
                    lat, lon, alt_km = eci_to_geodetic_spherical(r[0], r[1], r[2], t)

                path.append((lat, lon, alt_km))

        # Safe TLE epoch (prefer DB epoch; fall back to parse from line 1)
        tle_epoch_dt: Optional[datetime] = None
        db_epoch = getattr(tle, "epoch", None)
        if db_epoch:
            tle_epoch_dt = db_epoch if db_epoch.tzinfo else db_epoch.replace(tzinfo=timezone.utc)
        else:
            tle_epoch_dt = _tle_epoch_from_line1(line1_text)
        tle_epoch_iso = tle_epoch_dt.isoformat() if tle_epoch_dt else None

        results.append({
            "norad_id": nid,
            "t0_utc": t0.isoformat(),
            "tle_epoch_utc": tle_epoch_iso,
            "lat": lat0,            # stays real-time, not frozen
            "lon": lon0,
            "alt": alt0,
            "velocity": v0,
            "period_minutes": period_min,
            "dt_sec": dt_sec,
            "path": path
        })

    return {"at_utc": t0.isoformat(), "count": len(results), "results": results}









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

    # ✅ Return plain dicts; FastAPI validates against response_model
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
    # ✅ Return dict, not a Pydantic init
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
    curr_v = 0
    for i in range(samples + 1):
        t = start + timedelta(seconds=i * dt_sec)
        jd, fr = jday(t.year, t.month, t.day, t.hour, t.minute, t.second + t.microsecond * 1e-6)
        e, r, v = rec.sgp4(jd, fr)
        if e != 0 or r is None:
            continue
        lat, lon, alt_km = eci_to_geodetic_spherical(r[0], r[1], r[2], t)
        path.append((lat, lon, alt_km))
        curr_v = v

    lat0, lon0, alt0 = path[0] if path else (0.0, 0.0, 0.0)
    return {
        "norad_id": norad_id,
        "lat": lat0,
        "lon": lon0,
        "alt": alt0,
        "velocity": curr_v,
        "path": path,
    }





