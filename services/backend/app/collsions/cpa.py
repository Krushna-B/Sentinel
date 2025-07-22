import numpy as np
from datetime import datetime, timezone, timedelta

HORIZON = 48.0
HORIZON_S = 48.0
INTERVAL = 30.0
STORE = 10.0
ALERT = 1.0

def rows_to_arrays(rows):
    rows = np.asarray(rows,dtype=np.float64)
    id_a = rows[:,0].astype(np.int32)
    id_b = rows[:,1].astype(np.int32)
    rA = rows[:, 2:5]
    vA = rows[:, 5:8]
    rB = rows[:, 8:11]
    vB = rows[:, 11:14]
    return id_a, id_b, rA, vA, rB, vB


def cpa_grid_quadratic(rA,rB,vA,vB,dt,horizon = HORIZON*3600):
    N = rA.shape[0]
 
    time_grid = np.arange(0.0, horizon+1e-9, dt)


    rA_g = rA[:,None,:] +vA[:None,:] * time_grid[None,:,None] #(N,M,3)
    rB_g = rA[:,None,:] +vB[:None,:] * time_grid[None,:,None] #(N,M,3)
   
    d2 = np.sum((rB_g-rA_g)**2, axis=2)         #(N,M)
    k = np.argmin(d2, axis=1)                   #(N, ) k[i] = Grid point with smallest separation

    k0 = np.clip(k-1, 0, len(time_grid)-1)     # left neighbour
    k2 = np.clip(k+1, 0, len(time_grid)-1)     # right neighbour

    t0, t1, t2  = time_grid[k0], time_grid[k], time_grid[k2]      # (N,)
    d0, d1, d2_ = d2[np.arange(N), k0], d2[np.arange(N), k], d2[np.arange(N), k2]

    num   = d0 - d2_
    denom = d0 - 2*d1 + d2_
    t_star = t1 + 0.5 * dt * (num / denom)   # (N,) refined seconds
    t_star = np.clip(t_star, 0.0, horizon) # keep inside window
    d_min = np.linalg.norm((rB - rA) + (vB - vA) * t_star[:, None], axis=1)

    return t_star, d_min


# ida, idb, rA, vA, rB, vB = rows_to_arrays(rows)
# t_star, d_min = cpa_grid_quadratic(rA, vA, rB, vB, HORIZON)d


# now_utc = datetime.now(timezone.utc)

# print("\n=== SAMPLE CPA RESULTS (first 10 pairs) ===")
# for a, b, t_rel, d in zip(ida[:10], idb[:10],
#                           t_star[:10], d_min[:10]):
#     when = now_utc + timedelta(seconds=float(t_rel))
#     print(f"Pair {a:>6}/{b:<6} | miss = {d:6.3f} km"
#           f" | CPA in {t_rel/3600:6.2f} h"
#           f" ({when.isoformat(timespec='seconds')}Z)")


def cpa_analytic(rA, rB, vA, vB, horizon):
    """
    Analytic CPA: for each pair, t* = −(r·v)/(v·v), clipped to [0,horizon],
    then d_min = ||r + v t*||.
    """
    r_rel = rB - rA                    # (N,3)
    v_rel = vB - vA                    # (N,3)
    vv    = np.sum(v_rel*v_rel, axis=1)  # (N,)
    # avoid division by zero:
    t_star = np.zeros_like(vv)
    nonzero = vv > 1e-12
    t_star[nonzero] = -np.sum(r_rel[nonzero]*v_rel[nonzero], axis=1) / vv[nonzero]
    t_star = np.clip(t_star, 0.0, horizon)
    closest = r_rel + v_rel * t_star[:,None]  # (N,3)
    d_min   = np.linalg.norm(closest, axis=1)
    return t_star, d_min

async def process_batch(batch):
    """Consume one batch: compute CPA and print the first 5 results."""
    ida, idb, rA, vA, rB, vB = rows_to_arrays(batch)
    t_star, d_min = cpa_analytic(rA, rB, vA, vB, HORIZON_S)
    now = datetime.now(timezone.utc)

    print(f"\n>>> Processed batch of {len(batch)} candidates; sample CPA:")
    for a, b, t_rel, d in zip(ida[:5], idb[:5], t_star[:5], d_min[:5]):
        when = now + timedelta(seconds=float(t_rel))
        print(
            f"  Pair {a:>6}/{b:<6} | miss = {d:6.3f} km"
            + f" | CPA in {t_rel/3600:5.2f} h"
            + f" ({when.isoformat(timespec='seconds')}Z)"
        )
