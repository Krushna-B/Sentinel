"""
Quick one-shot test:
    • opens an asyncpg pool
    • runs the coarse-filter SQL once
    • prints how many rows came back and the first few
"""

import asyncio
from datetime import datetime, timedelta, timezone
import os
import asyncpg

DSN = os.getenv("PG_DSN", "postgresql://orbit:orbit@localhost:5432/orbit")
HORIZON_H = 48         

async def main():
    pool = await asyncpg.create_pool(dsn=DSN, min_size=1, max_size=4)

   
    
    t_min = (datetime.now(timezone.utc) - timedelta(minutes=5)).replace(tzinfo=None)
    t_max = (datetime.now(timezone.utc) + timedelta(hours=HORIZON_H)).replace(tzinfo=None)

    sql = open("services/backend/app/collsions/collision_candidates.sql").read()
    rows = await pool.fetch(sql, t_min, t_max)                 # $1, $2 filled

    print(f" Coarse filter returned {len(rows)} candidate rows\n")
    for r in rows[:3]:                                         
        print(dict(r))                                        

    await pool.close()

if __name__ == "__main__":
    asyncio.run(main())
