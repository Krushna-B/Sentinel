CREATE TABLE if NOT EXISTS collision_candidates (
    id SERIAL PRIMARY KEY,
    ida INT NOT NULL,
    idb INT NOT NULL,
    x_a FLOAT8, y_a FLOAT8, z_a FLOAT8,
    vx_a FLOAT8, vy_a FLOAT8, vz_a FLOAT8,
    x_b FLOAT8, y_b FLOAT8, z_b FLOAT8,
    vx_b FLOAT8, vy_b FLOAT8, vz_b FLOAT8,
    detection_time TIMESTAMPTZ DEFAULT now()
);
