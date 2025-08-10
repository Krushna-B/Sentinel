
import { getSatPoints } from "@/lib/api";
import GlobePane from "@/components/GlobePane";
import { GlobeHUD } from "@/components/GlobeHUD";

const displayNumber = 10000

export default async function Home(){

  const sats = await getSatPoints(displayNumber);
   const stats = {
    total: sats?.length ?? 0,
    updated5m: Math.floor((sats?.length ?? 0) * 0.13),
    alertsOpen: 7,
  };


  return (
    <div className="relative h-full">

      <GlobePane sats={sats}/>
     {/* <GlobeHUD stats={stats} /> */}
    </div>



  )

}