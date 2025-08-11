
import { getSatPoints } from "@/lib/api";
import GlobePane from "@/components/GlobePane";

const displayNumber = 10000

export default async function Home(){

  const sats = await getSatPoints(displayNumber);
   


  return (
    <div className="relative h-full">

      <GlobePane sats={sats}/>
    
    </div>



  )

}