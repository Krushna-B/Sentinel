import asyncio
import asyncpg
from datetime import datetime,timezone, timedelta

HORIZON = 48

async def get_candidates(pool):
    t_max = datetime.now(timezone.utc) + timedelta(hours=HORIZON)
    t_min = await pool.fetchval("Select last_t from Checkpoint")

    sql = open("services/backend/app/collsions/collision_candidates.sql").read()
    rows = pool.fetch(sql,t_max,t_min)
    
    print("Fetched", len(rows), "candidate rows")
    for r in rows[:5]:
            # Record behaves like both tuple and dict:
            print(dict(r))

    await pool.execute("""
        INSERT INTO checkpoint(last_t) VALUES ($1)
        ON CONFLICT (id) DO UPDATE SET last_t = EXCLUDED.last_t
    """, t_max)
    return rows