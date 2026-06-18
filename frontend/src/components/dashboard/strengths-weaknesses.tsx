import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Plus, Minus } from "lucide-react";

export function StrengthsWeaknesses({
  strengths,
  weaknesses,
}: {
  strengths: string[];
  weaknesses: string[];
}) {
  return (
    <div className="grid md:grid-cols-2 gap-5">
      <Card>
        <CardHeader>
          <CardTitle>Strengths</CardTitle>
        </CardHeader>
        <ul className="space-y-3">
          {strengths.map((s, i) => (
            <li key={i} className="flex gap-2.5 text-sm text-paper">
              <Plus size={16} className="text-verified shrink-0 mt-0.5" />
              {s}
            </li>
          ))}
        </ul>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Weaknesses</CardTitle>
        </CardHeader>
        <ul className="space-y-3">
          {weaknesses.map((w, i) => (
            <li key={i} className="flex gap-2.5 text-sm text-paper">
              <Minus size={16} className="text-flag shrink-0 mt-0.5" />
              {w}
            </li>
          ))}
        </ul>
      </Card>
    </div>
  );
}
