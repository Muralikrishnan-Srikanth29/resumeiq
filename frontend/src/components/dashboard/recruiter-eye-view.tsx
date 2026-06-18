"use client";

import { useEffect, useState } from "react";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { AlertTriangle, CheckCircle2 } from "lucide-react";
import { RecruiterEyeView } from "@/lib/types";

export function RecruiterEyeViewCard({ data }: { data: RecruiterEyeView }) {
  const [scanPos, setScanPos] = useState("10%");

  useEffect(() => {
    const t = setTimeout(() => setScanPos("90%"), 200);
    return () => clearTimeout(t);
  }, []);

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Recruiter Eye View</CardTitle>
          <Badge tone="signal">{data.confidence_score}/100 confidence</Badge>
        </div>
        <CardDescription>What a recruiter forms an opinion on in the first 10 seconds</CardDescription>
      </CardHeader>

      <div
        className="scan-line rounded-lg border border-line bg-[#0d111a] px-5 py-4 mb-5"
        style={{ "--scan-pos": scanPos } as React.CSSProperties}
      >
        <p className="text-paper text-sm leading-relaxed">{data.first_impression}</p>
      </div>

      <div className="grid md:grid-cols-2 gap-5">
        <div>
          <div className="flex items-center gap-2 mb-2.5">
            <CheckCircle2 size={16} className="text-verified" />
            <span className="text-xs uppercase tracking-wide text-slate-light font-medium">
              Positive signals
            </span>
          </div>
          <ul className="space-y-2">
            {data.positive_signals.map((signal, i) => (
              <li key={i} className="text-sm text-paper flex gap-2">
                <span className="text-verified">•</span>
                {signal}
              </li>
            ))}
          </ul>
        </div>
        <div>
          <div className="flex items-center gap-2 mb-2.5">
            <AlertTriangle size={16} className="text-flag" />
            <span className="text-xs uppercase tracking-wide text-slate-light font-medium">
              Likely rejection reasons
            </span>
          </div>
          <ul className="space-y-2">
            {data.rejection_reasons.map((reason, i) => (
              <li key={i} className="text-sm text-paper flex gap-2">
                <span className="text-flag">•</span>
                {reason}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </Card>
  );
}
