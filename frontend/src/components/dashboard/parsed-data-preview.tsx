import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ResumeJSON } from "@/lib/types";

export function ParsedDataPreview({ resume }: { resume: ResumeJSON }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>What we extracted</CardTitle>
        <CardDescription>
          Structured fields parsed from your resume — this is what the analysis runs on
        </CardDescription>
      </CardHeader>
      <div className="grid sm:grid-cols-2 gap-4 font-mono text-xs">
        <div>
          <span className="text-slate-light">name: </span>
          <span className="text-paper">&quot;{resume.name || "—"}&quot;</span>
        </div>
        <div>
          <span className="text-slate-light">experience_years: </span>
          <span className="text-signal">{resume.experience_years}</span>
        </div>
        <div>
          <span className="text-slate-light">email: </span>
          <span className="text-paper">&quot;{resume.email || "—"}&quot;</span>
        </div>
        <div>
          <span className="text-slate-light">sections_detected: </span>
          <span className="text-verified">{resume.sections_detected.length}</span>
        </div>
      </div>
      <div className="mt-4">
        <p className="text-xs uppercase tracking-wide text-slate-light font-medium mb-2">
          skills ({resume.skills.length})
        </p>
        <div className="flex flex-wrap gap-1.5">
          {resume.skills.slice(0, 20).map((s, i) => (
            <Badge key={i}>{s}</Badge>
          ))}
        </div>
      </div>
    </Card>
  );
}
