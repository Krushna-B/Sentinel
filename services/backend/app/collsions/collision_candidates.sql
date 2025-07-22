WITH latest AS(
    SELECT DISTINCT ON(id)
        id  AS sat_id,
        timestamp,
        x,y,z,vx,vy,vz
    FROM state_vectors
    WHERE timestamp BETWEEN $1 and $2   --$1 and $2 represent timestamps 
    ORDER BY id, timestamp DESC 
),
derived AS (
    SELECT
        sat_id,
        x, y, z, vx, vy, vz,

        sqrt(x*x + y*y + z*z) AS rho,        --sphereical coordinates (magnitude)
        atan2(y,x) AS lambda,                  -- longitude  (rad)
        acos(z / NULLIF(sqrt(x*x + y*y + z*z), 0)) AS phi   --inclination

      
        FROM latest
),

binned AS (              
    SELECT
      sat_id, x, y, z, vx, vy, vz,
     
      floor( (rho - 6378.137 - 160.0) / 25.0     
      )::int AS hbin,  -- altitude shell  : 25 km tall, start counting 160 km above Earth
     
      floor( (phi * 180/PI()) / 5.0 )              ::int AS ibin,    --inclination bin : 5° increments  (colat = 90° – inclination)
      
      floor( 
        mod(
           ((lambda * 180 / PI()) + 360.0)::numeric,   
            360::numeric                               
        ) / 5.0
        )::int AS rbin   -- RAAN bin        : 5° increments, wrap 0–360
      
    FROM derived
)
SELECT
    a.sat_id AS ida,
    b.sat_id AS idb,
    a.x  AS x_a,  a.y  AS y_a,  a.z  AS z_a,
    a.vx AS vx_a, a.vy AS vy_a, a.vz AS vz_a,

    b.x  AS x_b,  b.y  AS y_b,  b.z  AS z_b,
    b.vx AS vx_b, b.vy AS vy_b, b.vz AS vz_b    
FROM   binned a
JOIN   binned b
    ON   abs(a.hbin - b.hbin) <= 1      -- same altitude shell or neighbour
 AND  abs(a.ibin  - b.ibin)  <= 1      -- same incl. bucket  (±1 = 5° margin)
 AND  abs(a.rbin  - b.rbin)  <= 1      -- same RAAN bucket   (±1 = 5° margin)
 AND  a.sat_id < b.sat_id;             -- prevents (A,B) vs (B,A) duplicates


