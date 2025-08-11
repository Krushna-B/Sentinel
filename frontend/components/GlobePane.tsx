'use client';

import { useMemo, useState,useRef,useEffect } from 'react'
import dynamic from 'next/dynamic'
import { Sat, getSatDetails, getOrbit ,OrbitEntry, getOrbitsBulk} from '@/lib/api'
import * as THREE from 'three';
import { tleToOrbitPath, OrbitPath,   } from '@/lib/tleToOrbitPath';
import { getTLELatest } from '@/lib/api'
import GlobeCardHUD from './GlobeCardHUD';
const Globe = dynamic(() => import('react-globe.gl'), { ssr: false })


const R_EARTH_KM = 6371;    
const DOT_GEO = new THREE.SphereGeometry(0.9, 8, 8);       
const DOT_MAT = new THREE.MeshBasicMaterial({ color: 0xffffff });

type TleMap = Record<number, { line1: string; line2: string }>;
type TleRecord = { line1: string; line2: string };

interface GlobePaneProps {
  sats: Sat[];
  tles?: TleMap | null;
}

function normalizeLon(lon: number) {
 return ((lon + 180) % 360 + 360) % 360 - 180;
}

type PathPoint = { lat: number; lng: number; alt: number };
function splitByDateline(points: PathPoint[]) {
  const out: PathPoint[][] = [];
  let seg: PathPoint[] = [];
  for (let i = 0; i < points.length; i++) {
    const p = points[i];
    if (i > 0) {
      const prev = points[i - 1];
      if (Math.abs(p.lng - prev.lng) > 180) {
        if (seg.length > 1) out.push(seg);
        seg = [];
      }
    }
    seg.push(p);
  }
  if (seg.length > 1) out.push(seg);
  return out;
}


export default function GlobePane( { sats,tles}: GlobePaneProps) {
  

  // const objects = useMemo(
  //   () => sats.map(s => ({ id: s.norad_id, lat: s.lat, lng: s.lon, alt: (s.alt) / R_EARTH_KM })),
  //   [sats]
  // )
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const detailsCache = useRef(new Map<number, any>());
  const [details, setDetails] = useState<any | null>(null);

  const ids = useMemo(() => sats.map(s => s.norad_id), [sats]);
  const [bulkMap, setBulkMap] = useState<Map<number, OrbitEntry>>(new Map());

  useEffect(() => {
    if (ids.length === 0) return;

    let cancelled = false;

    const load = async () => {
      try {
        // just "now" values, no path
        const data = await getOrbitsBulk(ids, 1, 0);
        if (cancelled) return;
        const m = new Map<number, OrbitEntry>();
        for (const r of data.results) {
          if (!r.error) m.set(r.norad_id, r);
        }
        setBulkMap(m);
      } catch {
        if (!cancelled) setBulkMap(new Map());
      }
    };

    load();
    const id = setInterval(load, 10000); // light polling
    return () => { cancelled = true; clearInterval(id); };
  }, [ids]);

  const [selectedPath, setSelectedPath] = useState<[number, number, number][]>([]);
  const [liveSelected, setLiveSelected] = useState<{ lat: number; lon: number; altKm: number } | null>(null);
 useEffect(() => {
    setSelectedPath([]);

    if (selectedId == null) { setLiveSelected(null); return; }

    // seed HUD immediately from bulk "now" so it updates instantly
    const seed = bulkMap.get(selectedId);
    if (seed) setLiveSelected({ lat: seed.lat, lon: normalizeLon(seed.lon), altKm: seed.alt });

    let cancelled = false;

    const load = async () => {
      try {
        const data = await getOrbitsBulk([selectedId], 1, 400); // includes path
        if (cancelled) return;
        const rec = data.results[0];
        if (rec && !rec.error) {
          setLiveSelected({ lat: rec.lat, lon: normalizeLon(rec.lon), altKm: rec.alt });
          setSelectedPath(rec.path ?? []);
        } else {
          setSelectedPath([]);
        }
      } catch {
        if (!cancelled) setSelectedPath([]);
      }
    };

    load();
    const intId = setInterval(load, 1000);
    return () => { cancelled = true; clearInterval(intId); };
  }, [selectedId, bulkMap]);



  const handleObjectClick = (o: any) => {
    if (!o) return;
    const id = o.id as number;
    setSelectedId(prev => (prev === id ? null : id)); 
  };

  const handleOnClose = () => {
    setSelectedId(null);
    setDetails(null);
  };

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') handleOnClose(); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  // const objects = useMemo(
  //           () =>
  //         sats
  //         // .filter(s => s.norad_id !== selectedId) // NEW: remove selected from bulk
  //         .map(s => ({
  //         id: s.norad_id,
  //         lat: s.lat,
  //         lng: (s.lon),            // NEW: normalize lon
  //         alt: (s.alt) / R_EARTH_KM
  //         })),
  //         [sats, selectedId]
  //         );
  





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

  const objects = useMemo(() => {
    return sats.map(s => {
      const live = bulkMap.get(s.norad_id);
      const lat = live ? live.lat : s.lat;
      const lon = live ? live.lon : s.lon;
      const altKm = live ? live.alt : s.alt;
      return {
        id: s.norad_id,
        lat,
        lng: normalizeLon(lon),
        alt: (altKm ?? 0) / R_EARTH_KM,
        isSelected: s.norad_id === selectedId
      };
    });
  }, [sats, bulkMap, selectedId]);
  

    const orbits = useMemo(() => {
    if (!selectedPath.length) return [];
    const pts = selectedPath.map(([lat, lon, altKm]) => ({
      lat,
      lng: normalizeLon(lon),
      alt: altKm / R_EARTH_KM
    }));
    const segments = splitByDateline(pts);
    return segments.map((seg, i) => ({ id: `${selectedId}-seg-${i}`, points: seg }));
  }, [selectedPath, selectedId]);

  //TLE Handling for Path Creation
  // const tleCache = useRef(new Map<number, TleRecord>());
  // const [selectedTle, setSelectedTle] = useState<TleRecord | null>(null);
  // const tleAbortRef = useRef<AbortController | null>(null);

  // useEffect(() => {
  //   // cancel any in-flight TLE fetch when selection changes
  //   tleAbortRef.current?.abort();

  //   let cancelled = false;

  //   (async () => {
  //     if (selectedId == null) {
  //       setSelectedTle(null);
  //       return;
  //     }

  //     // Prefer prop map (if provided), else cache
  //     const fromProp = tles?.[selectedId] as TleRecord | undefined;
  //     const fromCache = tleCache.current.get(selectedId);
  //     let tle: TleRecord | undefined = fromProp || fromCache;

  //     // Fetch if needed
  //     if (!tle) {
  //       const ctrl = new AbortController();
  //       tleAbortRef.current = ctrl;
  //       try {
  //         const resp = await getTLELatest(selectedId, ctrl.signal).catch(() => null);
  //         if (resp && resp.line1 && resp.line2) {
  //           tle = { line1: resp.line1, line2: resp.line2 };
  //         }
  //       } catch {
  //         // ignore; tle stays undefined
  //       } finally {
  //         // clear our ref if this was the active controller
  //         if (tleAbortRef.current === ctrl) tleAbortRef.current = null;
  //       }
  //     }

  //     if (cancelled) return;

  //     if (tle) {
  //       tleCache.current.set(selectedId, tle);
  //       setSelectedTle(tle);
  //     } else {
  //       setSelectedTle(null);
  //     }
  //   })();

  //   return () => {
  //     cancelled = true;
  //   };
  // }, [selectedId, tles]);

  // Orbit for the selected satellite only (yellow)
  // const orbits: OrbitPath[] = useMemo(() => {
  //   if (selectedId == null || !selectedTle) return [];
  //   const path = tleToOrbitPath(selectedTle.line1, selectedTle.line2, 240);
  //   return path ? [path] : [];
  // }, [selectedId, selectedTle]);
 

  // type OrbitNow = { lat: number; lon: number; alt: number; path: [number, number, number][] };
  // const [orbitNow, setOrbitNow] = useState<OrbitNow | null>(null);
  // const hasOrbit = !!orbitNow;

  // useEffect(() => {
  //   if (selectedId == null) { setOrbitNow(null); return; }
  //   let cancelled = false;

  //   const load = async () => {
  //     try {
  //       const d = await getOrbit(selectedId, 1, 180);
  //       if (!cancelled) setOrbitNow({ lat: d.lat, lon: d.lon, alt: d.alt, path: d.path });
  //     } catch {
  //       if (!cancelled) setOrbitNow(null);
  //     }
  //   };

  //   load();
  //   const id = setInterval(load, 10_000); // light polling
  //   return () => { cancelled = true; clearInterval(id); };
  // }, [selectedId]);

  // // Selected dot rendered from the exact /orbit values
  // const selectedDot = useMemo(() => {
  //   if (!orbitNow || selectedId == null) return [];
  //   return [{
  //     id: selectedId,
  //     lat: orbitNow.lat,
  //     lng: normalizeLon(orbitNow.lon),
  //     alt: orbitNow.alt / R_EARTH_KM
  //   }];
  // }, [orbitNow, selectedId]);

  return (
    <div className="relative w-full h-[calc(100vh-64px)]">


    <Globe
      
      backgroundColor="#000"
      globeImageUrl="//unpkg.com/three-globe/example/img/earth-day.jpg"
      showAtmosphere={true}

      objectsData={objects}
      objectLat="lat"
      objectLng="lng"
      objectAltitude="alt"
      objectThreeObject={() => new THREE.Mesh(DOT_GEO, DOT_MAT)}
      onObjectClick={handleObjectClick} 
      onGlobeClick={() => handleOnClose()}
  
      pathsData={orbits}
      pathPoints="points"       
      pathPointLat="lat"
      pathPointLng="lng"
      pathPointAlt="alt"
      pathColor={() => "#FFD700"}
      pathStroke={2}   
      pathTransitionDuration={0} // no re-animate on state changes
   
    />
    <GlobeCardHUD
      objects={sats}
      selectedId={selectedId}
      details={details}
      live={liveSelected}
      onClose={handleOnClose}
    />
    
    </div>
  )
}





