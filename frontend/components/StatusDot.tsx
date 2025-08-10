"use client";




interface StatusDotsProps {
  okay: boolean
}

export function StatusDot({okay=true}:StatusDotsProps) {
  return (
    <span
      className={[
        "inline-flex h-2.5 w-2.5 items-center justify-center rounded-full",
        okay ? "bg-emerald-500" : "bg-red-500",
      ].join(" ")}
    />
  );
}