"use client";

import { useMemo, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem,
  DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger
} from "@/components/ui/dropdown-menu";
import {
  Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow
} from "@/components/ui/table";
import { Satellite, Filter, Upload, Eye, Plus } from "lucide-react";

type SatRow = {
  norad: number; name: string; orbit: "LEO"|"MEO"|"GEO"|"HEO";
  altKm: number; velKms: number; status: "active"|"decayed"|"unknown";
};

const SAMPLE: SatRow[] = [
  { norad: 223028, name: "SENTINEL-A1", orbit: "LEO", altKm: 525, velKms: 7.6, status: "active" },
  { norad: 241837, name: "SENTINEL-B2", orbit: "LEO", altKm: 535, velKms: 7.5, status: "active" },
  { norad: 39944,  name: "STARLINK-1201", orbit: "LEO", altKm: 550, velKms: 7.6, status: "active" },
  { norad: 40967,  name: "TEST-DRIFT", orbit: "HEO", altKm: 20000, velKms: 3.9, status: "unknown" },
];

export default function ObjectsPage() {
  const [q, setQ] = useState("");
  const [orbit, setOrbit] = useState<"ALL"|"LEO"|"MEO"|"GEO"|"HEO">("ALL");
  const [status, setStatus] = useState<"ALL"|"active"|"decayed"|"unknown">("ALL");

  const rows = useMemo(() => {
    return SAMPLE.filter(r =>
      (orbit === "ALL" || r.orbit === orbit) &&
      (status === "ALL" || r.status === status) &&
      (q === "" || r.name.toLowerCase().includes(q.toLowerCase()) || String(r.norad).includes(q))
    );
  }, [q, orbit, status]);

  return (
    <div className="h-full p-6">
      <div className="flex flex-wrap items-center gap-2">
        <div className="relative">
          <Input value={q} onChange={e=>setQ(e.target.value)} placeholder="Search NORAD or name…" className="w-72 pl-3" />
        </div>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline"><Filter className="mr-2 size-4" />Orbit: {orbit}</Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start">
            <DropdownMenuLabel>Orbit</DropdownMenuLabel>
            <DropdownMenuSeparator />
            {(["ALL","LEO","MEO","GEO","HEO"] as const).map(o=>(
              <DropdownMenuItem key={o} onClick={()=>setOrbit(o)}>{o}</DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline"><Filter className="mr-2 size-4" />Status: {status}</Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start">
            <DropdownMenuLabel>Status</DropdownMenuLabel>
            <DropdownMenuSeparator />
            {(["ALL","active","decayed","unknown"] as const).map(s=>(
              <DropdownMenuItem key={s} onClick={()=>setStatus(s)}>{s}</DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>

        <div className="ml-auto flex gap-2">
          <Button variant="outline"><Upload className="mr-2 size-4" />Import TLE</Button>
          <Button><Plus className="mr-2 size-4" />New Watchlist</Button>
        </div>
      </div>

    <div className="py-4">

    </div>
      <Card>
        <CardHeader className="flex-row items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Satellite className="size-4" /> Satellites
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableCaption>{rows.length} satellites</TableCaption>
            <TableHeader>
              <TableRow>
                <TableHead>NORAD</TableHead>
                <TableHead>Name</TableHead>
                <TableHead>Orbit</TableHead>
                <TableHead className="text-right">Alt (km)</TableHead>
                <TableHead className="text-right">Vel (km/s)</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.map(r=>(
                <TableRow key={r.norad}>
                  <TableCell>{r.norad}</TableCell>
                  <TableCell className="font-medium">{r.name}</TableCell>
                  <TableCell>{r.orbit}</TableCell>
                  <TableCell className="text-right">{r.altKm.toFixed(0)}</TableCell>
                  <TableCell className="text-right">{r.velKms.toFixed(2)}</TableCell>
                  <TableCell>
                    <Badge variant={r.status==="active"?"default":r.status==="decayed"?"destructive":"secondary"}>
                      {r.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <Button variant="ghost" size="sm"><Eye className="mr-1 size-4" />View</Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
