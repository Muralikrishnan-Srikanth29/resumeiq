import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { ProgressBar } from "@/components/ui/progress-bar";

export function HeatMapCard({ heatMap }: { heatMap: Record<string, number> }) {
  const entries = Object.entries(heatMap);
  if (entries.length === 0) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Resume Heat Map</CardTitle>
        <CardDescription>Section-by-section strength, scored independently</CardDescription>
      </CardHeader>
      <div className="space-y-4">
        {entries.map(([section, score]) => (
          <ProgressBar key={section} label={section.replace(/_/g, " ")} value={score} />
        ))}
      </div>
    </Card>
  );
}
