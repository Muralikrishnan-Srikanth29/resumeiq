import { Card } from "@/components/ui/card";
import { ScoreGauge } from "@/components/ui/score-gauge";
import { Badge } from "@/components/ui/badge";
import { AnalyzeResponse } from "@/lib/types";

export function DashboardMetrics({ result }: { result: AnalyzeResponse }) {
  const isMatching = result.mode === "matching" && result.match_scores;
  const gapCount =
    result.gaps.missing_skills.length +
    result.gaps.missing_certifications.length +
    result.gaps.missing_sections.length;

  const probabilityTone =
    result.ai.shortlist_probability === "High"
      ? "verified"
      : result.ai.shortlist_probability === "Medium"
      ? "signal"
      : "flag";

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <Card className="flex flex-col items-center justify-center">
        <ScoreGauge score={result.scores.resume_score} label="Resume Score" size="sm" />
      </Card>
      <Card className="flex flex-col items-center justify-center">
        <ScoreGauge score={result.scores.ats_score} label="ATS Score" size="sm" />
      </Card>
      {isMatching ? (
        <Card className="flex flex-col items-center justify-center">
          <ScoreGauge
            score={result.match_scores!.overall_match_score}
            label="Match Score"
            size="sm"
          />
        </Card>
      ) : (
        <Card className="flex flex-col items-center justify-center">
          <ScoreGauge
            score={result.ai.recruiter_eye_view.confidence_score}
            label="Recruiter Score"
            size="sm"
          />
        </Card>
      )}
      <Card className="flex flex-col items-center justify-center gap-3">
        <span className="font-display text-3xl font-semibold text-paper">{gapCount}</span>
        <span className="text-xs uppercase tracking-wide text-slate-light">Gaps Found</span>
        {isMatching && (
          <Badge tone={probabilityTone}>{result.ai.shortlist_probability} shortlist odds</Badge>
        )}
      </Card>
    </div>
  );
}
