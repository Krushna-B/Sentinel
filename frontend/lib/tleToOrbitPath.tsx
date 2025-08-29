import * as sat from 'satellite.js';
const R_EARTH_KM = 6371;

export type OrbitPoint = { lat: number; lng: number; alt: number };
export type OrbitPath  = { id: number; points: OrbitPoint[] };

export function tleToOrbitPath(tle1: string, tle2: string, samples = 400): OrbitPath | null {
  try {
    const rec = sat.twoline2satrec(tle1, tle2);
    const n = (rec as any).no_kozai ?? rec.no;            // rad/min
    if (!n) return null;

    const periodMin = (2 * Math.PI) / n;
    const t0 = new Date();
    const gmst0 = sat.gstime(t0);                          

    const points: OrbitPoint[] = [];
    for (let i = 0; i < samples; i++) {
      const t = new Date(t0.getTime() + (periodMin * 60 * 1000 * i) / samples);
      const pv = sat.propagate(rec, t);
      if (!pv?.position) continue;

      // Use the same gmst0 for every sample so you draw the orbit in one fixed frame
      const geo = sat.eciToGeodetic(pv.position, gmst0);

      points.push({
        lat: sat.degreesLat(geo.latitude),
        lng: sat.degreesLong(geo.longitude),
        alt: Math.max(0, geo.height / R_EARTH_KM),        
      });
    }
    return { id: Number(rec.satnum), points };
  } catch {
    return null;
  }
}
