"use client";

import { useMemo, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs,TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { Badge } from "@/components/ui/badge";
import { ChevronDown, Filter, MoreHorizontal } from "lucide-react";
import { SeverityBadge } from "@/components/SeverityBadge";

const SEVERITIES = ["critical", "high", "medium", "low"] as const;

const MOCK_ALERTS = Array.from({ length: 24 }, (_, i) => ({
  id: `A-${3200 + i}`,
  sev: (SEVERITIES[i % 4]) as (typeof SEVERITIES)[number],
  pair: `${20000 + i}/${24000 + (i * 3)}`,
  miss: (Math.random() * 500).toFixed(1),
  tca: `2025-08-09 ${String(10 + (i % 12)).padStart(2, "0")}:$${String(i % 60).padStart(2, "0")}Z`,
  status: i % 5 === 0 ? "muted" : i % 7 === 0 ? "resolved" : "open",
}));

export default function AlertsPage() {
  const [query, setQuery] = useState("");
  const [sev, setSev] = useState<string | "">("");
  const [tab, setTab] = useState("open");
  const [selected, setSelected] = useState<Set<string>>(new Set());

  const filtered = useMemo(() => {
    return MOCK_ALERTS.filter((a) =>
      (tab === "open" ? a.status === "open" : tab === "resolved" ? a.status === "resolved" : a.status === "muted") &&
      (sev ? a.sev === sev : true) &&
      (query ? `${a.id} ${a.pair}`.toLowerCase().includes(query.toLowerCase()) : true)
    );
  }, [query, sev, tab]);

  const toggle = (id: string) => {
    setSelected((s) => {
      const next = new Set(s);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  return (
    <div className="h-full p-6">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold">Alerts</h1>
          <p className="text-sm text-muted-foreground">Monitor close approaches and system notices.</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" className="rounded-xl"><Filter className="mr-2 h-4 w-4" /> Filters</Button>
          <Button className="rounded-xl">Acknowledge Selected</Button>
        </div>
      </div>

      <Card className="rounded-2xl">
        <CardHeader className="pb-3">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <CardTitle>Close Approach Alerts</CardTitle>
            <Tabs value={tab} onValueChange={setTab} className="w-full sm:w-auto">
              <TabsList className="rounded-xl">
                <TabsTrigger value="open">Open</TabsTrigger>
                <TabsTrigger value="resolved">Resolved</TabsTrigger>
                <TabsTrigger value="muted">Muted</TabsTrigger>
              </TabsList>
            </Tabs>
          </div>
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <Input placeholder="Search ID or pair…" value={query} onChange={(e) => setQuery(e.target.value)} className="h-9 w-full sm:w-60" />
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" className="rounded-xl">
                  Severity {sev ? <Badge className="ml-2 capitalize">{sev}</Badge> : <ChevronDown className="ml-2 h-4 w-4" />}
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => setSev("")}>All</DropdownMenuItem>
                {SEVERITIES.map((s) => (
                  <DropdownMenuItem key={s} onClick={() => setSev(s)} className="capitalize">
                    {s}
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-10">
                    <Checkbox aria-label="Select all" checked={selected.size && filtered.every((a) => selected.has(a.id))} onCheckedChange={(v) => {
                      if (v) setSelected(new Set(filtered.map((a) => a.id)));
                      else setSelected(new Set());
                    }} />
                  </TableHead>
                  <TableHead>ID</TableHead>
                  <TableHead>Severity</TableHead>
                  <TableHead>Pair</TableHead>
                  <TableHead className="text-right">Miss (km)</TableHead>
                  <TableHead>TCA</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="w-12"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.map((a) => (
                  <TableRow key={a.id} data-state={selected.has(a.id) ? "selected" : undefined}>
                    <TableCell>
                      <Checkbox aria-label={`Select ${a.id}`} checked={selected.has(a.id)} onCheckedChange={() => toggle(a.id)} />
                    </TableCell>
                    <TableCell className="font-medium">{a.id}</TableCell>
                    <TableCell><SeverityBadge level={a.sev as any} /></TableCell>
                    <TableCell className="tabular-nums">{a.pair}</TableCell>
                    <TableCell className="text-right tabular-nums">{a.miss}</TableCell>
                    <TableCell className="tabular-nums">{a.tca}</TableCell>
                    <TableCell className="capitalize">
                      <Badge variant={a.status === "open" ? "default" : "secondary"}>{a.status}</Badge>
                    </TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon" className="h-8 w-8">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem>View</DropdownMenuItem>
                          <DropdownMenuItem>Mark Resolved</DropdownMenuItem>
                          <DropdownMenuItem>Mute</DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>

          {/* Simple pager */}
          <div className="mt-4 flex items-center justify-between text-sm text-muted-foreground">
            <span>Showing {filtered.length} results</span>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" className="rounded-xl">Prev</Button>
              <Button variant="outline" size="sm" className="rounded-xl">Next</Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
