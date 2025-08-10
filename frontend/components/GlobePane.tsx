'use client';

import { useMemo, useState } from 'react'
import dynamic from 'next/dynamic'
import { Sat } from '@/lib/getSatellites'
import * as THREE from 'three';
const Globe = dynamic(() => import('react-globe.gl'), { ssr: false })

const R_EARTH_KM = 6371;    
const DOT_GEO = new THREE.SphereGeometry(0.9, 8, 8);       // << here
const DOT_MAT = new THREE.MeshBasicMaterial({ color: 0xffffff });



interface GlobePaneProps {
  sats: Sat[]
}

export default function GlobePane( { sats }: GlobePaneProps) {

  const objects = useMemo(
    () => sats.map(s => ({ id: s.norad_id, lat: s.lat, lng: s.lon, alt: (s.alt- R_EARTH_KM) / R_EARTH_KM })),
    [sats]
  )
  const [hoverId, setHoverId] = useState<number | null>(null)


  const hoverPath = useMemo(() => {
    if (hoverId == null) return []
    const sat = sats.find(s => s.norad_id === hoverId)
    if (!sat) return []
    return [
      {
        id: hoverId,
        path: sat.path.map(([lat, lon]) => ({ lat, lng: lon })),
      },
    ]
  }, [hoverId, sats])

  return (
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

  
      pathsData={hoverPath}
      pathPoints="path"
      pathPointLat="lat"
      pathPointLng="lng"
      pathColor={() => 'yellow'}
      pathStroke={1.5}

      onPointHover={p => setHoverId(p ? (p as any).id : null)}
    />
  )
}
