"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Separator } from "@/components/ui/separator";
import { Input } from "@/components/ui/input";
import { Download, Plus, Satellite, Activity, AlertTriangle } from "lucide-react";
import { Sparkline } from "@/components/Sparkline";
import { SeverityBadge } from "@/components/SeverityBadge";
import { StatusDot } from "@/components/StatusDot";

const trendData = Array.from({ length: 24 }, (_, i) => ({ time: `${i}:00`, value: 800 + Math.round(Math.sin(i / 3) * 60) + i * 2 }));

const recentAlerts = [
  { id: "A-3242", pair: "223028 / 241837", miss: 40.6, tca: "2025-08-09 12:10Z", sev: "high" },
  { id: "A-3243", pair: "33214 / 55621", miss: 122.3, tca: "2025-08-09 12:35Z", sev: "medium" },
  { id: "A-3244", pair: "11890 / 70012", miss: 8.4, tca: "2025-08-09 12:41Z", sev: "critical" },
];

export default function HomePage() {
  return (
    <div className="h-full p-6">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold">Home</h1>
          <p className="text-sm text-muted-foreground"> Overview and quick actions.</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" className="rounded-xl">
            <Download className="mr-2 h-4 w-4" /> Export
          </Button>
          <Button className="rounded-xl">
            <Plus className="mr-2 h-4 w-4" /> Add NORAD ID
          </Button>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
        {/* KPIs */}
        <Card className="rounded-2xl">
          <CardHeader>
            <CardTitle className="text-sm text-muted-foreground">Active Objects</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-end justify-between">
              <div>
                <div className="text-3xl font-semibold tabular-nums">12,842</div>
                <p className="text-xs text-muted-foreground">+1.2% vs yesterday</p>
              </div>
              <div className="h-16 w-40">
                <Sparkline data={trendData} />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="rounded-2xl">
          <CardHeader>
            <CardTitle className="text-sm text-muted-foreground">Close Approaches · 24h</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-end justify-between">
              <div>
                <div className="text-3xl font-semibold tabular-nums">58</div>
                <p className="text-xs text-muted-foreground">12 flagged as high risk</p>
              </div>
              <Badge variant="secondary" className="h-6 rounded-full">Live</Badge>
            </div>
          </CardContent>
        </Card>

        <Card className="rounded-2xl">
          <CardHeader>
            <CardTitle className="text-sm text-muted-foreground">System Status</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="flex items-center justify-between"><span className="flex items-center gap-2"><Satellite className="h-4 w-4" /> TLE Ingestor</span><StatusDot okay /></div>
            <div className="flex items-center justify-between"><span className="flex items-center gap-2"><Activity className="h-4 w-4" /> Propagator</span><StatusDot okay /></div>
            <div className="flex items-center justify-between"><span className="flex items-center gap-2"><Activity className="h-4 w-4" /> WebSocket</span><StatusDot okay={false} /></div>
            <div className="flex items-center justify-between"><span className="flex items-center gap-2"><Activity className="h-4 w-4" /> Database</span><StatusDot okay /></div>
          </CardContent>
        </Card>

        {/* Alerts & Activity */}
        <Card className="rounded-2xl md:col-span-2">
          <CardHeader className="flex-row items-center justify-between">
            <CardTitle>Recent Alerts</CardTitle>
            <Button variant="outline" size="sm" className="rounded-xl">View all</Button>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ID</TableHead>
                  <TableHead>Severity</TableHead>
                  <TableHead>Pair</TableHead>
                  <TableHead className="text-right">Miss (km)</TableHead>
                  <TableHead>TCA</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {recentAlerts.map((a) => (
                  <TableRow key={a.id}>
                    <TableCell className="font-medium">{a.id}</TableCell>
                    <TableCell><SeverityBadge level={a.sev as any} /></TableCell>
                    <TableCell>{a.pair}</TableCell>
                    <TableCell className="text-right tabular-nums">{a.miss.toFixed(1)}</TableCell>
                    <TableCell>{a.tca}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        <Card className="rounded-2xl">
          <CardHeader>
            <CardTitle>Activity</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-muted-foreground">
            <div className="flex items-center gap-2"><AlertTriangle className="h-4 w-4" /> New high-risk approach detected</div>
            <Separator />
            <div className="flex items-center gap-2"><Satellite className="h-4 w-4" /> 1,234 objects updated</div>
            <Separator />
            <div className="flex items-center gap-2"><Activity className="h-4 w-4" /> Kafka pipeline healthy</div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
