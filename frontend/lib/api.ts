// lib/api.ts2
import * as sat from "satellite.js";

const API = process.env.NEXT_PUBLIC_API_BASE;

const R_EARTH_KM = 6371.0;                 
const RAD2DEG = 180 / Math.PI;

export type SVLatest = {
  norad_id: number;

  timestamp: string;
  x: number; y: number; z: number;
  vx: number; vy: number; vz: number;
};

export type Sat = {
  norad_id: number;

  lat: number;       
  lon: number;        
  alt: number;        
  path: [number, number, number][]; 
};

function normalizeLonDeg(deg: number) {
  return ((deg + 180) % 360 + 360) % 360 - 180; 
}

export function eciToGeodeticSpherical(
  r: { x: number; y: number; z: number },
  isoTs: string
) {
  const t = new Date(isoTs);
  const gmst = sat.gstime(t);        // radians

  // ECI -> ECEF rotation about Z by +GMST
  const cosG = Math.cos(gmst), sinG = Math.sin(gmst);
  const x =  cosG * r.x + sinG * r.y;
  const y = -sinG * r.x + cosG * r.y;
  const z =  r.z;

  const rxy = Math.hypot(x, y);
  const rmag = Math.hypot(rxy, z);

  const lat = Math.atan2(z, rxy) * RAD2DEG;
  const lon = normalizeLonDeg(Math.atan2(y, x) * RAD2DEG);
  const alt = rmag - R_EARTH_KM;

  return { lat, lon, alt };
}




export async function getLatestSV(limit = 20000): Promise<SVLatest[]> {
  const url = new URL(`${API}/state-vectors/latest`);
  url.searchParams.set("limit", String(limit));
  const r = await fetch(url.toString(), { cache: "no-store" });
  if (!r.ok) throw new Error("getLatestSV failed");
  return r.json();
}

// 2) Points for the globe (lat/lon/alt), derived from latest ECI
export async function getSatPoints(limit = 20000): Promise<Sat[]> {
  const rows = await getLatestSV(limit);
  return rows.map((r) => {
    const g = eciToGeodeticSpherical({ x: r.x, y: r.y, z: r.z }, r.timestamp);
    return {
      norad_id: r.norad_id,
      lat: g.lat,
      lon: g.lon,
      alt: g.alt,
      path: [], // compute on hover (client) or fetch via getOrbit()
    };
  });
}


export async function getTLELatest(norad: number, signal?: AbortSignal) {
  const url = `${API}/satellites/${norad}/tle/latest`;
  try {
    const r = await fetch(url, { cache: "no-store", signal });
    if (!r.ok) {
      const txt = await r.text().catch(() => "");
      console.warn("TLE not ok:", url, r.status, txt);
      throw new Error(`no TLE for ${norad} (${r.status})`);
    }
    return r.json() as Promise<{ norad_id: number; epoch: string; line1: string; line2: string }>;
  } catch (e: any) {
    if (e?.name === "AbortError") {
      // hover moved away; ignore quietly
      console.debug("TLE fetch aborted for", norad);
      return null;
    }
    console.error("TLE fetch failed:", url, e);
    throw e;
  }
}


export async function getOrbit(norad: number, periods = 1, samples = 180) {
  const url = new URL(`${API}/satellites/${norad}/orbit`);
  url.searchParams.set("periods", String(periods));
  url.searchParams.set("samples", String(samples));
  const r = await fetch(url.toString(), { cache: "no-store" });
  if (!r.ok) throw new Error("orbit fetch failed");
  return r.json() as Promise<{ norad_id: number; lat: number; lon: number; alt: number; velocity: [number, number, number]; path: [number, number, number][] }>;
}

export async function getSatDetails(norad: number) {
  const r = await fetch(`${API}/satellites/${norad}`, { cache: "no-store" });
  if (!r.ok) throw new Error("no satellite " + norad);
  return r.json() as Promise<{
    norad_id: number;
    name: string | null;
    cospar_id: string | null;
    object_type: string | null;
    country_code: string | null;
    launch_date: string | null;
  }>;
}


export type OrbitEntry = {
  norad_id: number;
  t0_utc?: string;
  tle_epoch_utc?: string;
  lat: number;
  lon: number;
  alt: number; // km
  velocity?: [number, number, number];
  period_minutes?: number;
  dt_sec?: number;
  path?: [number, number, number][];
  error?: string;
};


export async function getOrbitsBulk(
  ids: number[],
  periods = 1,
  samples = 200,
  at?: string // ISO string optional
): Promise<{ at_utc: string; count: number; results: OrbitEntry[] }> {
  const url = new URL(`${API}/satellites/orbits`);
  url.searchParams.set("ids", ids.join(","));
  url.searchParams.set("periods", String(periods));
  url.searchParams.set("samples", String(samples));
  if (at) url.searchParams.set("at", at);
  const r = await fetch(url.toString(), { cache: "no-store" });
  if (!r.ok) throw new Error("getOrbitsBulk failed");
  return r.json();
}