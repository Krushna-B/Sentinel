
from __future__ import annotations
import math
from typing import Union, Any, Tuple

import numpy as np

# Earth GM μ (WGS-84)  [km³ / s²]
MU = 398_600.4418



Num = Union[float, np.floating[Any]]


def state_to_elements(r_vec: Tuple[Num, Num, Num],
                      v_vec: Tuple[Num, Num, Num]) -> Tuple[float, float, float, float, float, float]:
    r = np.asarray(r_vec, dtype=float)
    v = np.asarray(v_vec, dtype=float)

    r_norm = np.linalg.norm(r)
    v_norm = np.linalg.norm(v)

    # Specific angular momentum h = r × v
    h = np.cross(r, v)
    h_norm = np.linalg.norm(h)

    # Inclination i
    i = math.acos(h[2] / h_norm)

    # Node vector n = k × h
    n = np.cross([0.0, 0.0, 1.0], h)
    n_norm = np.linalg.norm(n)

    # Eccentricity vector
    e_vec = (np.cross(v, h) / MU) - (r / r_norm)
    e = np.linalg.norm(e_vec)

    # Semi-major axis a
    a = 1.0 / (2.0 / r_norm - v_norm**2 / MU)

    # RAAN Ω
    Ω = 0.0 if n_norm == 0 else math.acos(n[0] / n_norm)
    if n[1] < 0:
        Ω = 2.0 * math.pi - Ω

    # Argument of periapsis ω
    ω = 0.0
    if n_norm and e > 1e-10:
        ω = math.acos(np.dot(n, e_vec) / (n_norm * e))
        if e_vec[2] < 0:
            ω = 2.0 * math.pi - ω

    # True anomaly ν
    ν = math.acos(np.dot(e_vec, r) / (e * r_norm)) if e > 1e-10 else 0.0
    if np.dot(r, v) < 0:
        ν = 2.0 * math.pi - ν

    # Mean anomaly M0
    cosE = (e + math.cos(ν)) / (1 + e * math.cos(ν))
    sinE = math.sin(ν) * math.sqrt(1 - e**2) / (1 + e * math.cos(ν))
    E = math.atan2(sinE, cosE)
    M0 = (E - e * math.sin(E)) % (2.0 * math.pi)

    return float(a), float(e), float(i), float(Ω), float(ω), float(M0)


# 2. Solve Kepler’s equation  E − e sinE = M

def kepler_E(M: Num, e: Num, tol: float = 1e-8) -> float:
    # Cast once so all downstream math is plain float
    M = float(M)
    e = float(e)

    E: float = M        
    for _ in range(15):
        f  = E - e * math.sin(E) - M
        f1 = 1.0 - e * math.cos(E)
        dE = -f / f1    
        E += dE
        if abs(dE) < tol:
            break
    return E % (2.0 * math.pi)


# 3. Elements ► ECI position at mean anomaly M

def elements_to_r(a: Num, e: Num, i: Num,
                  Ω: Num, ω: Num, M: Num) -> np.ndarray:
    """Return r_eci [km] for given mean anomaly M (rad)."""
    a, e, i, Ω, ω, M = map(float, (a, e, i, Ω, ω, M))

    E = kepler_E(M, e)
    # Perifocal coordinates
    x_p = a * (math.cos(E) - e)
    y_p = a * math.sqrt(1 - e**2) * math.sin(E)
    r_perif = np.array([x_p, y_p, 0.0])

    # Rotation: perifocal → ECI
    cosΩ, sinΩ = math.cos(Ω), math.sin(Ω)
    cosω, sinω = math.cos(ω), math.sin(ω)
    cosi, sini = math.cos(i), math.sin(i)

    R = np.array([
        [cosΩ*cosω - sinΩ*sinω*cosi,  -cosΩ*sinω - sinΩ*cosω*cosi,  sinΩ*sini],
        [sinΩ*cosω + cosΩ*sinω*cosi,  -sinΩ*sinω + cosΩ*cosω*cosi, -cosΩ*sini],
        [sinω*sini,                   cosω*sini,                   cosi]
    ])
    return R @ r_perif  # (3,) ndarray


# 4. ECI ► latitude / longitude  (spherical, no Earth rotation)

def eci_to_latlon(r_eci: np.ndarray,*, with_alt: bool = False):
    x, y, z = map(float, r_eci)
    hyp = math.hypot(x, y)
    lon = math.degrees(math.atan2(y, x))  # −180…+180
    lat = math.degrees(math.atan2(z, hyp))
    if not with_alt:
        return lat, lon
    
    r_mag = math.sqrt(x*x + y*y + z*z)
    
    return lat, lon, r_mag

def eci_to_lla(r_eci: np.ndarray) -> Tuple[float, float, float]:
  
    x, y, z = map(float, r_eci)
    hyp = math.hypot(x, y)
    lon = math.degrees(math.atan2(y, x))  # −180…+180
    lat = math.degrees(math.atan2(z, hyp))
   
    
    r_mag = math.sqrt(x*x + y*y + z*z)
    
    return lat, lon, r_mag
