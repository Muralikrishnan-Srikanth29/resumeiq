"use client";

import { useState } from "react";
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { InterviewQuestionSet } from "@/lib/types";

const CATEGORIES: { key: keyof InterviewQuestionSet; label: string }[] = [
  { key: "technical", label: "Technical" },
  { key: "behavioral", label: "Behavioral" },
  { key: "leadership", label: "Leadership" },
  { key: "project_based", label: "Project-based" },
];

export function InterviewReadinessCard({ data }: { data: InterviewQuestionSet }) {
  const firstAvailable = CATEGORIES.find((c) => data[c.key]?.length > 0)?.key ?? "technical";
  const [active, setActive] = useState<keyof InterviewQuestionSet>(firstAvailable);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Interview Readiness</CardTitle>
        <CardDescription>Questions likely to come up, generated from your actual experience</CardDescription>
      </CardHeader>

      <div className="flex gap-1 mb-4 rounded-lg bg-line/40 p-1 w-fit overflow-x-auto">
        {CATEGORIES.map((cat) => (
          <button
            key={cat.key}
            onClick={() => setActive(cat.key)}
            className={cn(
              "px-3.5 py-1.5 rounded-md text-sm font-medium transition-colors whitespace-nowrap",
              active === cat.key ? "bg-signal text-ink" : "text-slate-light hover:text-paper"
            )}
          >
            {cat.label}
          </button>
        ))}
      </div>

      <ul className="space-y-3">
        {(data[active] || []).length === 0 ? (
          <li className="text-sm text-slate-light">No questions generated for this category.</li>
        ) : (
          data[active].map((q, i) => (
            <li key={i} className="flex gap-3 text-sm text-paper">
              <span className="font-mono text-slate-light shrink-0">{String(i + 1).padStart(2, "0")}</span>
              {q}
            </li>
          ))
        )}
      </ul>
    </Card>
  );
}
