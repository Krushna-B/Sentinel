
import { getSatPoints, getLatestSV, getOrbitsBulk, Sat } from "@/lib/api";
import GlobePane from "@/components/GlobePane";

const displayNumber = 1000

export default async function Home(){
  const rows = await getLatestSV(displayNumber);
  const ids = rows.map(r => r.norad_id);

  const bulk = await getOrbitsBulk(ids, 1, 0);
  const map = new Map(bulk.results.filter(r => !r.error).map(r => [r.norad_id, r]));

  // const sats = await getSatPoints(displayNumber);
   

const sats: Sat[] = ids.map(id => {
    const b = map.get(id);
    return {
      norad_id: id,
      lat: b?.lat ?? 0,
      lon: b?.lon ?? 0,
      alt: b?.alt ?? 0,
      path: []
    };
  });

  return (
    <div className="relative h-full">

      <GlobePane sats={sats}/>
    
    </div>



  )

}