"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import {
  Home,
  Globe2,
  Satellite,
  Radar,
  Bell,
  Activity,
  Map,
  Database,
  Menu,
  Sun,
  MoonStar,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Separator } from "@/components/ui/separator";



const NAV_SECTIONS: {
  label: string;
  items: { href: string; label: string; icon: React.ElementType }[];
}[] = [
  {
    label: "Core",
    items: [
      { href: "/home", label: "Home", icon: Home },
      { href: "/globe", label: "3D Globe", icon: Globe2 },
      { href: "/objects", label: "Satellites", icon: Satellite },
      { href: "/tracks", label: "Tracks", icon: Map },
      { href: "/events", label: "Alerts", icon: Bell },
    ],
  },
  {
    label: "Analysis",
    items: [
      { href: "/cpa", label: "CPA", icon: Radar },
      { href: "/metrics", label: "Metrics", icon: Activity },
      { href: "/data", label: "Data", icon: Database },
    ],
  },
];

// Theme toggle stub (swap with your theme logic if you use next-themes)
function ThemeToggle() {
  return (
    <div className="flex items-center justify-center">
      <Button size="icon" variant="ghost" aria-label="Toggle theme">
        <Sun className="h-5 w-5 dark:hidden" />
        <MoonStar className="hidden h-5 w-5 dark:block" />
      </Button>
    </div>
  );
}

function ActivePill() {
  return (
    <motion.span
      layoutId="active-pill"
      className="absolute inset-0 rounded-xl bg-primary/10 ring-1 ring-primary/30"
      transition={{ type: "spring", stiffness: 420, damping: 30 }}
    />
  );
}

function RailItem({
  href,
  label,
  icon: Icon,
  active,
}: {
  href: string;
  label: string;
  icon: React.ElementType;
  active: boolean;
}) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Link href={href} aria-label={label} className="relative block">
          <span
            className={`
              group relative flex h-11 w-11 items-center justify-center rounded-xl transition
              ${active
                ? "text-primary"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            {active && <ActivePill />}
            <Icon className="relative z-[1] h-5 w-5" />
          </span>
        </Link>
      </TooltipTrigger>
      <TooltipContent side="right" sideOffset={8} className="px-2 py-1 text-xs">
        {label}
      </TooltipContent>
    </Tooltip>
  );
}

export default function AppSidebar() {
  const pathname = usePathname();

  return (
    <TooltipProvider delayDuration={50}>
      <aside
        className={
          "fixed inset-y-0 left-0 z-40 hidden border-r bg-background/80 backdrop-blur supports-[backdrop-filter]:bg-background/60 md:flex w-[4.25rem] flex-col items-center justify-between px-2 py-3"
        }
      >
        
        <div className="flex w-full flex-col items-center gap-3">
          <Button size="icon" variant="ghost" className="h-10 w-10" aria-label="Open menu">
            <Menu className="h-5 w-5" />
          </Button>

       
          <Separator className="my-2"/>

        
          <nav className="flex w-full flex-col items-center gap-1">
            {NAV_SECTIONS[0].items.map((item) => (
              <RailItem
                key={item.href}
                href={item.href}
                label={item.label}
                icon={item.icon}
                active={pathname === item.href}
              />
            ))}
          </nav>

          <Separator className="my-2" />

         
          <nav className="flex w-full flex-col items-center gap-1">
            {NAV_SECTIONS[1].items.map((item) => (
              <RailItem
                key={item.href}
                href={item.href}
                label={item.label}
                icon={item.icon}
                active={pathname === item.href}
              />
            ))}
          </nav>
        </div>

   
        <div className="flex w-full flex-col items-center gap-2">
          <ThemeToggle />
        </div>

      </aside>

      {/* Spacer so content doesn't sit under the rail */}
      <div className="hidden md:block" style={{ width: "4.25rem" }} />
    </TooltipProvider>
  );
}

