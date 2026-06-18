"use client";

import { useState } from "react";
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { generateRoadmap } from "@/lib/api";
import { RoadmapResponse } from "@/lib/types";
import { Loader2 } from "lucide-react";

export function CareerRoadmapCard({ resumeId }: { resumeId: string }) {
  const [currentRole, setCurrentRole] = useState("");
  const [targetRole, setTargetRole] = useState("");
  const [roadmap, setRoadmap] = useState<RoadmapResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleGenerate() {
    if (!currentRole.trim() || !targetRole.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const result = await generateRoadmap({ resumeId, currentRole, targetRole });
      setRoadmap(result);
    } catch {
      setError("Couldn't generate a roadmap right now. Try again in a moment.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Career Growth Analysis</CardTitle>
        <CardDescription>Plan the path from where you are to where you want to be</CardDescription>
      </CardHeader>

      <div className="flex flex-col sm:flex-row gap-3 mb-5">
        <input
          value={currentRole}
          onChange={(e) => setCurrentRole(e.target.value)}
          placeholder="Current role, e.g. QA Engineer"
          className="flex-1 rounded-lg border border-line bg-[#0d111a] px-4 py-2.5 text-sm text-paper placeholder:text-slate-light/60 focus:border-signal focus:outline-none"
        />
        <input
          value={targetRole}
          onChange={(e) => setTargetRole(e.target.value)}
          placeholder="Target role, e.g. Project Manager"
          className="flex-1 rounded-lg border border-line bg-[#0d111a] px-4 py-2.5 text-sm text-paper placeholder:text-slate-light/60 focus:border-signal focus:outline-none"
        />
        <Button onClick={handleGenerate} disabled={loading || !currentRole.trim() || !targetRole.trim()}>
          {loading ? <Loader2 size={16} className="animate-spin" /> : "Generate roadmap"}
        </Button>
      </div>

      {error && <p className="text-sm text-flag mb-4">{error}</p>}

      {roadmap && (
        <div className="space-y-6">
          <div className="grid sm:grid-cols-2 gap-5">
            <div>
              <p className="text-xs uppercase tracking-wide text-slate-light font-medium mb-2.5">
                Skill gaps
              </p>
              <div className="flex flex-wrap gap-2">
                {roadmap.skill_gaps.map((s, i) => (
                  <Badge key={i} tone="flag">
                    {s}
                  </Badge>
                ))}
              </div>
            </div>
            <div>
              <p className="text-xs uppercase tracking-wide text-slate-light font-medium mb-2.5">
                Certification gaps
              </p>
              <div className="flex flex-wrap gap-2">
                {roadmap.certification_gaps.map((c, i) => (
                  <Badge key={i} tone="signal">
                    {c}
                  </Badge>
                ))}
              </div>
            </div>
          </div>

          <div>
            <p className="text-xs uppercase tracking-wide text-slate-light font-medium mb-3">
              90-day roadmap
            </p>
            <div className="grid sm:grid-cols-3 gap-4">
              {roadmap.roadmap_90_day.map((phase, i) => (
                <div key={i} className="rounded-lg border border-line bg-[#0d111a] p-4">
                  <p className="font-display text-sm font-semibold text-signal mb-2">
                    {phase.phase}
                  </p>
                  <ul className="space-y-1.5">
                    {phase.focus_areas.map((f, j) => (
                      <li key={j} className="text-xs text-paper">
                        {f}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </Card>
  );
}
