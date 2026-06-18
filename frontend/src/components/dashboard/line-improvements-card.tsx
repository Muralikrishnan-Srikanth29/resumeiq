import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { ArrowRight } from "lucide-react";
import { LineImprovement } from "@/lib/types";

export function LineImprovementsCard({ items }: { items: LineImprovement[] }) {
  if (items.length === 0) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Line-by-Line Improvements</CardTitle>
        <CardDescription>Specific rewrite suggestions for your weakest bullet points</CardDescription>
      </CardHeader>
      <div className="space-y-5">
        {items.map((item, i) => (
          <div key={i} className="rounded-lg border border-line bg-[#0d111a] p-4">
            <p className="font-mono text-sm text-flag/90 mb-2">&ldquo;{item.current}&rdquo;</p>
            <div className="flex items-center gap-2 my-2">
              <ArrowRight size={14} className="text-slate-light" />
              <span className="text-xs text-slate-light uppercase tracking-wide">
                {item.issue}
              </span>
            </div>
            <p className="font-mono text-sm text-verified mb-2">&ldquo;{item.improved}&rdquo;</p>
            <p className="text-xs text-slate-light">{item.reason}</p>
          </div>
        ))}
      </div>
    </Card>
  );
}
