import { throwDeprecation } from "process"

export type Sat = {
  norad_id: number
  lat: number
  lon: number,
  alt: number;
  path: [number, number][]
}


export async function getSatellites(limit=100){

 
    const res = await fetch(`${process.env.BACKEND_URL}/satellites/?limit=${limit}&step=60`)
    
    if (!res.ok) throw new Error("Datafetch Failed"); 
    const data = (await res.json()) as Sat[];
    
    console.log(data)
    return data
   
}