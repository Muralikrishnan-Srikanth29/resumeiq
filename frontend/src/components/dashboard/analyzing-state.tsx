"use client";

import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";

const STEPS = [
  "Extracting text",
  "Structuring resume data",
  "Running rule-based scoring",
  "Matching against job requirements",
  "Generating recruiter insights",
];

export function AnalyzingState() {
  const [stepIndex, setStepIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setStepIndex((i) => Math.min(i + 1, STEPS.length - 1));
    }, 1100);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex flex-col items-center justify-center gap-6 py-24">
      <Loader2 size={32} className="text-signal animate-spin" />
      <div className="text-center">
        <p className="font-display text-lg text-paper">{STEPS[stepIndex]}</p>
        <p className="text-sm text-slate-light mt-1">This usually takes 5-15 seconds</p>
      </div>
    </div>
  );
}
