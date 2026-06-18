import { cn } from "@/lib/utils";

interface ProgressBarProps {
  value: number;
  label: string;
  className?: string;
}

function colorForScore(score: number): string {
  if (score >= 75) return "bg-verified";
  if (score >= 50) return "bg-signal";
  return "bg-flag";
}

export function ProgressBar({ value, label, className }: ProgressBarProps) {
  const clamped = Math.max(0, Math.min(100, value));
  return (
    <div className={cn("flex flex-col gap-1.5", className)}>
      <div className="flex items-center justify-between text-sm">
        <span className="text-paper capitalize">{label}</span>
        <span className="font-mono text-slate-light">{Math.round(clamped)}</span>
      </div>
      <div className="h-2 rounded-full bg-line overflow-hidden">
        <div
          className={cn("h-full rounded-full transition-all duration-700", colorForScore(clamped))}
          style={{ width: `${clamped}%` }}
        />
      </div>
    </div>
  );
}
