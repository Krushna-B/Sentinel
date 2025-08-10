import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Bell, Search } from "lucide-react";

export function TopBar() {
  return (
    <header className="sticky top-0 z-10 flex h-14 items-center gap-3 border-b bg-background/70 px-4 backdrop-blur">
      <div className="flex-1 min-w-0 flex items-center gap-3">
        <Search className="h-4 w-4" />
        <Input placeholder="Search satellites, NORAD, events…" className="h-9 w-full max-w-xl" />
      </div>
      <div className="flex items-center gap-2">
        <Button variant="outline" size="sm" className="rounded-xl">
          <Bell className="mr-2 h-4 w-4" /> Alerts
        </Button>
      </div>
    </header>
  );
}