# Sentinel

LEO satillete positions and orbit visualization. Ingests TLEs, propagates orbits, and serves real-time satillete details via a FastAPI backend on AWS Lambda + API Gateway, a Neon Postgres database, and a Next.js/React 3-D globe.

---

## Overview

Sentinel continuously fetches Two-Line Elements (TLEs), stores historical ephemerides, propagates state vectors (x, y, z, vx, vy, vz), and exposes a clean API and web UI to understand where thousands of objects are and where they’re headed.

- Serverless backend on **AWS Lambda**
- **Neon** (managed Postgres) for storage (SSL required)
- **EventBridge** schedules for ingestion/propagation (cron without always-on servers)
- **Next.js/React** front end (e.g., Vercel) with a **react-globe.gl / Three.js** visualization
- Scales to **28k+ objects**; ~**2.7M state-vector epochs/day**

---

## Features

- FastAPI API layer: latest vectors, per-object TLEs, and bulk orbit sampling
- SGP4 propagation to compute ECI/ECEF positions and derived lat/lon/alt
- Historical storage of objects, TLEs, and propagated state vectors in Postgres
- Copy-paste curl examples and a minimal local dev story
- Container-optional: run locally with Uvicorn, deploy serverless to Lambda

---

## Tech Stack

- Backend: Python, FastAPI, SQLAlchemy, SGP4, Mangum (ASGI→Lambda)
- Data: Neon (PostgreSQL)
- Frontend: Next.js, React, TailwindCSS, react-globe.gl, Three.js
- Cloud: AWS Lambda, EventBridge (schedules)
