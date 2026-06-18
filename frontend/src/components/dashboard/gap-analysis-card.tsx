import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { GapAnalysis } from "@/lib/types";

export function GapAnalysisCard({ gaps }: { gaps: GapAnalysis }) {
  const sections = [
    { label: "Exact skill matches", items: gaps.exact_skill_matches, tone: "verified" as const },
    { label: "Missing skills", items: gaps.missing_skills, tone: "flag" as const },
    { label: "Missing certifications", items: gaps.missing_certifications, tone: "flag" as const },
    { label: "Missing keywords", items: gaps.missing_keywords, tone: "neutral" as const },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Gap Analysis</CardTitle>
        <CardDescription>What this resume has and doesn&apos;t have, relative to the role</CardDescription>
      </CardHeader>
      <div className="space-y-5">
        {sections.map(
          (section) =>
            section.items.length > 0 && (
              <div key={section.label}>
                <p className="text-xs uppercase tracking-wide text-slate-light font-medium mb-2.5">
                  {section.label}
                </p>
                <div className="flex flex-wrap gap-2">
                  {section.items.map((item, i) => (
                    <Badge key={i} tone={section.tone}>
                      {item}
                    </Badge>
                  ))}
                </div>
              </div>
            )
        )}
      </div>
    </Card>
  );
}
