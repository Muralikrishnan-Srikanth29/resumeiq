"use client";

import { cn } from "@/lib/utils";

interface ScoreGaugeProps {
  score: number;
  label: string;
  size?: "sm" | "md" | "lg";
  className?: string;
}

function colorForScore(score: number): string {
  if (score >= 75) return "#1abc9c";
  if (score >= 50) return "#ff6b4a";
  return "#e63950";
}

export function ScoreGauge({ score, label, size = "md", className }: ScoreGaugeProps) {
  const dimensions = { sm: 88, md: 120, lg: 160 }[size];
  const stroke = { sm: 6, md: 8, lg: 10 }[size];
  const radius = (dimensions - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const clamped = Math.max(0, Math.min(100, score));
  const offset = circumference - (clamped / 100) * circumference;
  const color = colorForScore(clamped);

  return (
    <div className={cn("flex flex-col items-center gap-2", className)}>
      <div className="relative" style={{ width: dimensions, height: dimensions }}>
        <svg width={dimensions} height={dimensions} className="-rotate-90">
          <circle
            cx={dimensions / 2}
            cy={dimensions / 2}
            r={radius}
            fill="none"
            stroke="#232838"
            strokeWidth={stroke}
          />
          <circle
            cx={dimensions / 2}
            cy={dimensions / 2}
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth={stroke}
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            style={{ transition: "stroke-dashoffset 800ms cubic-bezier(0.16,1,0.3,1)" }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="font-display text-2xl font-semibold text-paper">
            {Math.round(clamped)}
          </span>
        </div>
      </div>
      <span className="text-xs uppercase tracking-wide text-slate-light text-center">
        {label}
      </span>
    </div>
  );
}
