"use client";

import { ResponsiveContainer, LineChart, Line, Tooltip, XAxis, YAxis } from "recharts";

interface SparklineProps{
      data:{
        time:string,
        value:number
      }[]
}

export function Sparkline( {data} :SparklineProps) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={data} margin={{ top: 6, right: 8, left: 0, bottom: 0 }}>
        <XAxis dataKey="time" hide />
        <YAxis hide domain={["dataMin - 10", "dataMax + 10"]} />
        <Tooltip cursor={false} formatter={(v: number) => v.toLocaleString()} labelFormatter={() => ""} />
        <Line type="monotone" dataKey="value" dot={false} strokeWidth={2} />
      </LineChart>
    </ResponsiveContainer>
  );
}