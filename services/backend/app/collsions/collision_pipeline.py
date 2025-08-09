import asyncio
from datetime import datetime, timedelta, timezone
import os
import asyncpg
import numpy as np
from fetch_candidates import get_candidates, store_candidates

DSN       = os.getenv("PG_DSN", "postgresql://orbit:orbit@localhost:5432/orbit")
HORIZON_H = 48          # hours
HORIZON_S = HORIZON_H * 3600  # seconds


async def get_db_pool(min_size=1, max_size=4):
  return await asyncpg.create_pool(dsn=DSN, min_size=min_size, max_size=max_size)

async def fetch_collision_candidates(pool, t_min, t_max):


    sql = open("services/backend/app/collsions/collision_candidates.sql").read()
    return await pool.fetch(sql, t_min, t_max)




async def main():
    pool = await get_db_pool()
    async with pool:
        rows = await get_candidates(pool)

        if rows:
            await store_candidates(pool,rows)
            # print(f"Stored {len(rows)} collision candidates.")
    await pool.close()

if __name__ == "__main__":
    asyncio.run(main())
