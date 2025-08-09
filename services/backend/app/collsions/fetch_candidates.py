
from datetime import datetime,timezone, timedelta

HORIZON = 48
WINDOW = 10
async def get_candidates(pool):
    t_min = await pool.fetchval("Select last_t from Checkpoint")
    t_min  = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=WINDOW)  # go back WINDOW hours
    t_max = t_min + timedelta(hours=HORIZON)
    
    sql = open("services/backend/app/collsions/collision_candidates.sql").read()
    rows = await pool.fetch(sql,t_min,t_max)

    # print("T_min:", t_min, "T_max:", t_max)
    # print("Fetched", len(rows), "candidate rows")
    
    await pool.execute("""
        INSERT INTO checkpoint(last_t) VALUES ($1)
        ON CONFLICT (id) DO UPDATE SET last_t = EXCLUDED.last_t
    """, t_max)
    return rows

async def store_candidates(pool, rows):
    records = [
        (
            int(row["ida"]), int(row["idb"]),
            row["x_a"], row["y_a"], row["z_a"],
            row["vx_a"], row["vy_a"], row["vz_a"],
            row["x_b"], row["y_b"], row["z_b"],
            row["vx_b"], row["vy_b"], row["vz_b"],
        )
        for row in rows
    ]
    sql = open("services/backend/app/collsions/store_collision_candidates.sql").read()
    await pool.execute(sql)
    
    await pool.executemany(""" 
        INSERT INTO collision_candidates (
            ida, idb,
            x_a, y_a, z_a, vx_a, vy_a, vz_a,
            x_b, y_b, z_b, vx_b, vy_b, vz_b
        )
        VALUES (
            $1, $2,
            $3, $4, $5, $6, $7, $8,
            $9, $10, $11, $12, $13, $14
        )
    """, records)
