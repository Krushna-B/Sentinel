'use client';

import { useMemo, useState,useRef,useEffect } from 'react'
import dynamic from 'next/dynamic'
import { Sat,getSatDetails } from '@/lib/api'
import * as THREE from 'three';
import * as sat from 'satellite.js'
import { getTLELatest } from '@/lib/api'
const Globe = dynamic(() => import('react-globe.gl'), { ssr: false })


const R_EARTH_KM = 6371;    
const DOT_GEO = new THREE.SphereGeometry(0.9, 8, 8);       // << here
const DOT_MAT = new THREE.MeshBasicMaterial({ color: 0xffffff });

type OrbitPt = { lat: number; lng: number; alt: number } 

function periodMinutesFromTLE(line2: string) {
  const mmRevPerDay = parseFloat(line2.slice(52, 63));
  return 1440 / mmRevPerDay;
}

async function buildOrbit(line1: string, line2: string, samples = 240): Promise<OrbitPt[]> {
  const rec = sat.twoline2satrec(line1, line2);
  const periodMin = rec.no && Number.isFinite(rec.no) ? (2 * Math.PI) / (rec.no as number) : periodMinutesFromTLE(line2);
  const dtSec = (periodMin * 60) / samples;
  const start = new Date();

  const pts: OrbitPt[] = [];
  for (let i = 0; i <= samples; i++) {
    const t = new Date(start.getTime() + i * dtSec * 1000);
    const pv = sat.propagate(rec, t);
    if (!pv?.position) continue;
    const gmst = sat.gstime(t);
    const gd = sat.eciToGeodetic(pv.position as sat.EciVec3<number>, gmst);
    // clamp altitude a bit just for visuals (lines too far out look odd)
    const altFrac = Math.max(0.02, Math.min((gd.height ?? 0) / R_EARTH_KM, 0.35));
    pts.push({ lat: sat.degreesLat(gd.latitude), lng: sat.degreesLong(gd.longitude), alt: altFrac });
  }
  return pts;
}
function llaToVec3(lat: number, lon: number, altFrac: number, globeRadius: number) {
  const r = globeRadius * (1 + altFrac);
  const phi = (90 - lat) * Math.PI / 180;      // polar angle
  const theta = (lon + 180) * Math.PI / 180;   // azimuth
  return new THREE.Vector3(
    -r * Math.sin(phi) * Math.cos(theta),
     r * Math.cos(phi),
     r * Math.sin(phi) * Math.sin(theta)
  );
}


interface GlobePaneProps {
  sats: Sat[]
}

export default function GlobePane( { sats }: GlobePaneProps) {
  const globeRef = useRef<any>(null);

  const objects = useMemo(
    () => sats.map(s => ({ id: s.norad_id, lat: s.lat, lng: s.lon, alt: (s.alt) / R_EARTH_KM })),
    [sats]
  )
  const [selectedId, setSelectedId] = useState<number | null>(null);

  const tleCache = useRef(new Map<number, { line1: string; line2: string }>());
  const orbitVertsCache = useRef(new Map<number, THREE.Vector3[]>()); // cache vectors
  const detailsCache = useRef(new Map<number, any>());
  
  const [customOrbits, setCustomOrbits] = useState<{ id: number; vertices: THREE.Vector3[] }[]>([]);
  const [details, setDetails] = useState<any | null>(null);

  const handleObjectClick = (o: any) => {
    if (!o) return;
    const id = o.id as number;
    setSelectedId(prev => (prev === id ? null : id)); // toggle
  };

  const clearSelection = () => {
    setSelectedId(null);
    setCustomOrbits([]);
    setDetails(null);
  };
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') clearSelection(); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      if (selectedId == null) { setDetails(null); return; }
      if (detailsCache.current.has(selectedId)) {
        setDetails(detailsCache.current.get(selectedId));
        return;
      }
      try {
        const d = await getSatDetails(selectedId);
        detailsCache.current.set(selectedId, d);
        if (!cancelled) setDetails(d);
      } catch {
        if (!cancelled) setDetails(null);
      }
    })();
    return () => { cancelled = true; };
  }, [selectedId]);

  

  
  useEffect(() => {
    const controller = new AbortController();
    let cancelled = false;

    (async () => {
      const id = selectedId;
      if (id == null) { setCustomOrbits([]); return; }

      // cached vertices?
      const cached = orbitVertsCache.current.get(id);
      if (cached) { setCustomOrbits([{ id, vertices: cached }]); return; }

      try {
        let tle = tleCache.current.get(id);
        if (!tle) {
          const t = await getTLELatest(id, controller.signal);
          if (!t) return; // aborted or not ok
          tle = { line1: t.line1, line2: t.line2 };
          tleCache.current.set(id, tle);
        }

        const pts = await buildOrbit(tle.line1, tle.line2, 240);
        const gr = globeRef.current?.getGlobeRadius?.() ?? 100; // fallback radius
        const verts = pts.map(p => llaToVec3(p.lat, p.lng, p.alt, gr));

        if (!cancelled) {
          orbitVertsCache.current.set(id, verts);
          setCustomOrbits([{ id, vertices: verts }]);
        }
      } catch {
        if (!cancelled) setCustomOrbits([]);
      }
    })();

    return () => { cancelled = true; controller.abort(); };
  }, [selectedId]);


  function CardHUD() {
  if (selectedId == null) return null;
  const obj = objects.find(o => o.id === selectedId);

  return (
    <div className="pointer-events-none fixed top-4 right-4 z-50">
      <div className="pointer-events-auto w-[88vw] max-w-[420px] min-w-[280px]
                      p-4 rounded-xl border border-white/10 bg-black/80 backdrop-blur
                      shadow-xl">
        <div className="flex items-start justify-between gap-3">
          <div className="space-y-1.5">
            <div className="text-sm font-semibold leading-tight">
              {details?.name ?? "Unknown object"}
            </div>

            <div className="text-xs text-neutral-300">
              NORAD: <span className="font-medium">{selectedId}</span>
              {details?.cospar_id && (
                <> · COSPAR: <span className="font-medium">{details.cospar_id}</span></>
              )}
            </div>
             {details?.object_type && (
              <div className="text-xs text-neutral-400">
                Object Type: {details.object_type}
              </div>
            )}
            {details?.launch_date && (
              <div className="text-xs text-neutral-400">
                Launch: {new Date(details.launch_date).toISOString().slice(0,10)}
              </div>
            )}

            {obj && (
              <div className="text-xs mt-1">
                lat <span className="font-medium">{obj.lat.toFixed(2)}°</span>,{" "}
                lon <span className="font-medium">{obj.lng.toFixed(2)}°</span>,{" "}
                alt <span className="font-medium">{(obj.alt * R_EARTH_KM).toFixed(0)} km</span>
              </div>
            )}
          </div>

          <button
            className="shrink-0 text-[11px] px-2.5 py-1 rounded-md
                       bg-white/10 hover:bg-white/20 active:bg-white/25 transition"
            onClick={clearSelection}
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

  return (
    <div className="relative w-full h-[calc(100vh-64px)]">


    <Globe
      
      backgroundColor="#000"
      // globeImageUrl="//unpkg.com/three-globe/example/img/earth-blue-marble.jpg"
      globeImageUrl="//unpkg.com/three-globe/example/img/earth-day.jpg"
      bumpImageUrl="//unpkg.com/three-globe/example/img/earth-topology.png"
      // earth-dark.jpg
      showAtmosphere={true}

      objectsData={objects}
      objectLat="lat"
      objectLng="lng"
      objectAltitude="alt"
      objectThreeObject={() => new THREE.Mesh(DOT_GEO, DOT_MAT)}
      onObjectClick={handleObjectClick} 
      onGlobeClick={() => clearSelection()}
  


      customLayerData={customOrbits}
        customThreeObject={(d: any) => {
          const geom = new THREE.BufferGeometry().setFromPoints(d.vertices);
          const mat = new THREE.LineBasicMaterial({ color: 0xffff00 });
          return new THREE.Line(geom, mat);
        }}
        customThreeObjectUpdate={(obj: any, d: any) => {
          obj.geometry.setFromPoints(d.vertices);
          return obj;
        }}
      // pathsData={selectedPath}
      // pathPoints="path"
      // pathPointLat="lat"
      // pathPointLng="lng"
      // pathPointAlt="alt" 
      // pathColor={() => 'yellow'}
      // pathStroke={1.5}

   
    />
     <CardHUD />
    </div>
  )
}





