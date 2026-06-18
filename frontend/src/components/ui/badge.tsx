import { cn } from "@/lib/utils";
import { HTMLAttributes } from "react";

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  tone?: "neutral" | "verified" | "flag" | "signal";
}

export function Badge({ className, tone = "neutral", ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium",
        tone === "neutral" && "bg-white/5 text-slate-light border border-line",
        tone === "verified" && "bg-verified/10 text-verified border border-verified/30",
        tone === "flag" && "bg-flag/10 text-flag border border-flag/30",
        tone === "signal" && "bg-signal/10 text-signal border border-signal/30",
        className
      )}
      {...props}
    />
  );
}
