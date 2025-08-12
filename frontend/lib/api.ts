// lib/api.ts2
import * as sat from "satellite.js";

const API = process.env.NEXT_PUBLIC_API_BASE;
const DEFAULT_HEADERS = { "ngrok-skip-browser-warning": "true" as const };
const baseInit: RequestInit = { cache: "no-store", headers: DEFAULT_HEADERS };

// -------- Types --------
export type SVLatest = {
  norad_id: number;

  timestamp: string;
  x: number; y: number; z: number;
  vx: number; vy: number; vz: number;
};

export type Sat = {
  norad_id: number;

  lat: number;        // degrees
  lon: number;        // degrees
  alt: number;        // km above surface
  path: [number, number, number][]; // [lat, lon, alt_km] (empty until you draw orbit)
};

// -------- Helpers --------
function eciToGeodeticKm(r: { x: number; y: number; z: number }, isoTs: string) {
  const t = new Date(isoTs);
  const gmst = sat.gstime(t);
  const gd = sat.eciToGeodetic(r as any, gmst);
  return {
    lat: sat.degreesLat(gd.latitude),
    lon: sat.degreesLong(gd.longitude),
    alt: (gd.height ?? 0), // km above surface
  };
}

// -------- API calls --------

// 1) Latest ECI per satellite (raw)
export async function getLatestSV(limit = 8000): Promise<SVLatest[]> {
  const url = new URL(`${API}/state-vectors/latest`);
  url.searchParams.set("limit", String(limit));
  const r = await fetch(url.toString(), baseInit);
  if (!r.ok) throw new Error("getLatestSV failed");
  return r.json();
}

// 2) Points for the globe (lat/lon/alt), derived from latest ECI
export async function getSatPoints(limit = 8000): Promise<Sat[]> {
  const rows = await getLatestSV(limit);
  return rows.map((r) => {
    const g = eciToGeodeticKm({ x: r.x, y: r.y, z: r.z }, r.timestamp);
    return {
      norad_id: r.norad_id,
      lat: g.lat,
      lon: g.lon,
      alt: g.alt,
      path: [], // compute on hover (client) or fetch via getOrbit()
    };
  });
}

// 3) Latest TLE (for client-side orbit)
export async function getTLELatest(norad: number, signal?: AbortSignal) {
  const url = `${API}/satellites/${norad}/tle/latest`;
  try {
    const r = await fetch(url, { ...baseInit, signal });
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

// (Optional) 4) Server-side orbit (use this instead of client compute if you like)
export async function getOrbit(norad: number, periods = 1, samples = 180) {
  const url = new URL(`${API}/satellites/${norad}/orbit`);
  url.searchParams.set("periods", String(periods));
  url.searchParams.set("samples", String(samples));
  const r = await fetch(url.toString(), baseInit);
  if (!r.ok) throw new Error("orbit fetch failed");
  return r.json() as Promise<{ norad_id: number; lat: number; lon: number; alt: number; path: [number, number, number][] }>;
}

export async function getSatDetails(norad: number) {
  const r = await fetch(`${API}/satellites/${norad}`, baseInit);
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