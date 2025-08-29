import * as sat from "satellite.js";

const API = process.env.NEXT_PUBLIC_API_BASE;
const DEFAULT_HEADERS = { "ngrok-skip-browser-warning": "true" as const };
const baseInit: RequestInit = { cache: "no-store", headers: DEFAULT_HEADERS };


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
  path?: [number, number, number][]; 
};

export async function getSatPoints(limit = 20000): Promise<Sat[]> {
  const url = new URL(`${API}/satellites/positions/all`);
  url.searchParams.set("limit", String(limit));

  const r = await fetch(url.toString(), baseInit);
if (!r.ok) {
    // Log details so we can see status and any backend error message
    let body = "";
    try { body = await r.text(); } catch {}
    console.error("getSatPoints failed", { url, status: r.status, body });
    throw new Error("getSatPoints failed");
  }

  const rows = (await r.json()) as { norad_id: number; lat: number; lon: number; alt: number }[];

  return rows.map((row) => ({
    norad_id: row.norad_id,
    lat: row.lat,
    lon: row.lon,
    alt: row.alt,
    path: [], 
  }));
}

// Latest TLE (for client-side orbit)
export async function getTLELatest(norad: number, signal?: AbortSignal) {
  const url = (`${API}/satellites/${norad}/tle/latest`);
  console.log(url)
  try {
    const r = await fetch(url.toString());
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
  const r = await fetch(url.toString(), baseInit);
  if (!r.ok) throw new Error("orbit fetch failed");
  return r.json() as Promise<{ norad_id: number; lat: number; lon: number; alt: number; path: [number, number, number][] }>;
}

export async function getSatDetails(norad: number) {
  const r = await fetch(`${API}/satellites/${norad}`);
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