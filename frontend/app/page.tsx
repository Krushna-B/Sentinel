
import { getSatellites } from "@/lib/getSatellites";
import GlobePane from "@/components/GlobePane";


const displayNumber = 9999

export default async function Home(){

  const sats = await getSatellites(displayNumber);

  return (
  <GlobePane sats={sats}>

  </GlobePane>
  )

}