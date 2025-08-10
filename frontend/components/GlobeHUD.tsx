"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { Play, Pause, Rewind, FastForward, Filter, RefreshCw, Globe2 } from "lucide-react";
import { useState } from "react";

export function GlobeHUD({
  stats,
}: {
  stats: { total: number; updated5m: number; alertsOpen: number };
}) {
  const [playing, setPlaying] = useState(true);

  return (
    <>
      {/* Top-left stats */}
      <div className="pointer-events-none absolute left-4 top-4 z-10 grid gap-3 sm:grid-cols-3">
        <HUDStat title="Objects" value={stats.total.toLocaleString()} icon={<Globe2 className="h-4 w-4" />} />
        <HUDStat title="Updated · 5m" value={stats.updated5m.toLocaleString()} />
        <HUDStat title="Open Alerts" value={String(stats.alertsOpen)} badge="Live" />
      </div>

      {/* Bottom center transport */}
      <div className="absolute inset-x-0 bottom-4 z-10 mx-auto flex w-full max-w-xl items-center justify-center">
        <Card className="w-full rounded-2xl border bg-background/70 backdrop-blur">
          <CardContent className="flex items-center justify-between gap-2 p-2">
            <div className="flex items-center gap-2">
              <Button variant="outline" size="icon" className="rounded-xl" onClick={() => {}}>
                <Rewind className="h-4 w-4" />
              </Button>
              <Button
                variant="default"
                size="icon"
                className="rounded-xl"
                onClick={() => setPlaying((v) => !v)}
              >
                {playing ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
              </Button>
              <Button variant="outline" size="icon" className="rounded-xl" onClick={() => {}}>
                <FastForward className="h-4 w-4" />
              </Button>
            </div>
            <div className="flex items-center gap-2">
              <Sheet>
                <SheetTrigger asChild>
                  <Button variant="outline" className="rounded-xl">
                    <Filter className="mr-2 h-4 w-4" /> Filters
                  </Button>
                </SheetTrigger>
                <SheetContent side="right" className="w-96">
                  <SheetHeader>
                    <SheetTitle>Globe Filters</SheetTitle>
                  </SheetHeader>
                  <div className="mt-4 space-y-3 text-sm">
                    <div className="flex items-center justify-between">
                      <span>Show Orbits</span>
                      <Badge variant="secondary">Soon</Badge>
                    </div>
                    <Separator />
                    <div className="flex items-center justify-between">
                      <span>Show Constellations</span>
                      <Badge variant="secondary">Soon</Badge>
                    </div>
                    <Separator />
                    <div className="flex items-center justify-between">
                      <span>Particles Layer</span>
                      <Badge>On</Badge>
                    </div>
                  </div>
                </SheetContent>
              </Sheet>
              <Button variant="outline" className="rounded-xl" onClick={() => {}}>
                <RefreshCw className="mr-2 h-4 w-4" /> Refresh
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </>
  );
}

function HUDStat({ title, value, icon, badge }: { title: string; value: string; icon?: React.ReactNode; badge?: string }) {
  return (
    <Card className="pointer-events-auto rounded-2xl border bg-background/70 backdrop-blur">
      <CardHeader className="p-3 pb-0">
        <CardTitle className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
          {icon}
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent className="p-3 pt-1">
        <div className="flex items-baseline gap-2">
          <span className="text-xl font-semibold tabular-nums">{value}</span>
          {badge && <Badge>{badge}</Badge>}
        </div>
      </CardContent>
    </Card>
  );
}