"use client";

import { Badge } from "@/components/ui/badge";


interface SeverityBadgeProps{
  level: "low" | "medium" | "high" | "critical"
}

export function SeverityBadge({level} : SeverityBadgeProps) {
  const map: Record<string, string> = {
    low: "bg-muted text-foreground",
    medium: "bg-yellow-500/20 text-yellow-600",
    high: "bg-orange-500/20 text-orange-600",
    critical: "bg-red-500/20 text-red-600",
  };
  return <Badge className={`capitalize ${map[level]}`}>{level}</Badge>;
}
