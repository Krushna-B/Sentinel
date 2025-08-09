
import { getSatellites } from "@/lib/getSatellites";
import GlobePane from "@/components/GlobePane";


const displayNumber = 1000

export default async function Home(){

  const sats = await getSatellites(displayNumber);

  return (
    <div className="w-screen">

      <GlobePane sats={sats}/>
    </div>



  )

}