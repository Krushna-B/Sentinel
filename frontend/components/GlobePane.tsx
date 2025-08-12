'use client';

import { useMemo, useState,useRef,useEffect } from 'react'
import dynamic from 'next/dynamic'
import { Sat, getSatDetails } from '@/lib/api'
import * as THREE from 'three';
import { tleToOrbitPath, OrbitPath } from '@/lib/tleToOrbitPath';
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

export default function GlobePane( { sats,tles}: GlobePaneProps) {
  const objects = useMemo(
    () => sats.map(s => ({ id: s.norad_id, lat: s.lat, lng: s.lon, alt: (s.alt) / R_EARTH_KM })),
    [sats]
  )
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const detailsCache = useRef(new Map<number, any>());
  const [details, setDetails] = useState<any | null>(null);

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

  // TLE Handling for Path Creation

  const tleCache = useRef(new Map<number, TleRecord>());
  const [selectedTle, setSelectedTle] = useState<TleRecord | null>(null);
  const tleAbortRef = useRef<AbortController | null>(null);
  useEffect(() => {
    // cancel any in-flight TLE fetch when selection changes
    tleAbortRef.current?.abort();

    let cancelled = false;

    (async () => {
      if (selectedId == null) {
        setSelectedTle(null);
        return;
      }

      // Prefer prop map (if provided), else cache
      const fromProp = tles?.[selectedId] as TleRecord | undefined;
      const fromCache = tleCache.current.get(selectedId);
      let tle: TleRecord | undefined = fromProp || fromCache;

      // Fetch if needed
      if (!tle) {
        const ctrl = new AbortController();
        tleAbortRef.current = ctrl;
        try {
          const resp = await getTLELatest(selectedId, ctrl.signal).catch(() => null);
          if (resp && resp.line1 && resp.line2) {
            tle = { line1: resp.line1, line2: resp.line2 };
          }
        } catch {
          // ignore; tle stays undefined
        } finally {
          // clear our ref if this was the active controller
          if (tleAbortRef.current === ctrl) tleAbortRef.current = null;
        }
      }

      if (cancelled) return;

      if (tle) {
        tleCache.current.set(selectedId, tle);
        setSelectedTle(tle);
      } else {
        setSelectedTle(null);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [selectedId, tles]);

  const orbits: OrbitPath[] = useMemo(() => {
    if (selectedId == null || !selectedTle) return [];
    const path = tleToOrbitPath(selectedTle.line1, selectedTle.line2, 240);
    return path ? [path] : [];
  }, [selectedId, selectedTle]);
 
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
      // onGlobeClick={() => handleOnClose()}
  
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
      onClose={handleOnClose}
    />
    
    </div>
  )
}





