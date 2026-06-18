"use client";

import { useState } from "react";
import { ResumeInput } from "@/components/input/resume-input";
import { JDInput } from "@/components/input/jd-input";
import { Button } from "@/components/ui/button";
import { AnalyzingState } from "@/components/dashboard/analyzing-state";
import { DashboardMetrics } from "@/components/dashboard/dashboard-metrics";
import { RecruiterEyeViewCard } from "@/components/dashboard/recruiter-eye-view";
import { HeatMapCard } from "@/components/dashboard/heat-map-card";
import { StrengthsWeaknesses } from "@/components/dashboard/strengths-weaknesses";
import { GapAnalysisCard } from "@/components/dashboard/gap-analysis-card";
import { LineImprovementsCard } from "@/components/dashboard/line-improvements-card";
import { InterviewReadinessCard } from "@/components/dashboard/interview-readiness-card";
import { ParsedDataPreview } from "@/components/dashboard/parsed-data-preview";
import { CareerRoadmapCard } from "@/components/dashboard/career-roadmap-card";
import { GrowthTrackerCard } from "@/components/dashboard/growth-tracker-card";
import { analyze, analyzeByResumeId, uploadResumeFile, APIError } from "@/lib/api";
import { AnalyzeResponse, ResumeJSON } from "@/lib/types";
import { ScanLine } from "lucide-react";

type AppState = "input" | "analyzing" | "results";

export default function Home() {
  const [appState, setAppState] = useState<AppState>("input");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [pastedResumeText, setPastedResumeText] = useState("");
  const [jdText, setJdText] = useState("");
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [parsedResume, setParsedResume] = useState<ResumeJSON | null>(null);
  const [error, setError] = useState<string | null>(null);

  const hasInput = selectedFile !== null || pastedResumeText.trim().length >= 200;

  async function handleAnalyze() {
    setError(null);
    setAppState("analyzing");
    try {
      let response: AnalyzeResponse;

      if (selectedFile) {
        const uploadResult = await uploadResumeFile(selectedFile);
        setParsedResume(uploadResult.resume);
        response = await analyzeByResumeId({
          resumeId: uploadResult.resume_id,
          jdText: jdText.trim() || undefined,
        });
      } else {
        response = await analyze({
          resumeText: pastedResumeText,
          jdText: jdText.trim() || undefined,
        });
      }

      setResult(response);
      setAppState("results");
    } catch (err) {
      const message =
        err instanceof APIError
          ? err.message
          : "Something went wrong while analyzing your resume. Please try again.";
      setError(message);
      setAppState("input");
    }
  }

  function handleStartOver() {
    setAppState("input");
    setSelectedFile(null);
    setPastedResumeText("");
    setJdText("");
    setResult(null);
    setParsedResume(null);
    setError(null);
  }

  return (
    <div className="min-h-screen">
      <header className="border-b border-line">
        <div className="max-w-5xl mx-auto px-6 py-5 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <ScanLine size={22} className="text-signal" />
            <span className="font-display text-lg font-semibold text-paper">ResumeIQ</span>
          </div>
          {appState === "results" && (
            <Button variant="ghost" size="sm" onClick={handleStartOver}>
              New analysis
            </Button>
          )}
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-12">
        {appState === "input" && (
          <div>
            <div className="mb-10">
              <h1 className="font-display text-3xl sm:text-4xl font-semibold text-paper leading-tight max-w-2xl">
                See your resume the way a recruiter does — in the 10 seconds before they decide.
              </h1>
              <p className="text-slate-light mt-3 max-w-xl">
                Upload or paste your resume. Add a job description for a match score, or leave it
                blank for a general evaluation. No account needed.
              </p>
            </div>

            <div className="space-y-8">
              <section>
                <h2 className="font-display text-sm uppercase tracking-wide text-slate-light mb-3">
                  01 — Your resume
                </h2>
                <ResumeInput
                  onFileSelected={(file) => {
                    setSelectedFile(file);
                    setPastedResumeText("");
                  }}
                  onTextChange={(text) => {
                    setPastedResumeText(text);
                    setSelectedFile(null);
                  }}
                  pastedText={pastedResumeText}
                  selectedFile={selectedFile}
                  onClearFile={() => setSelectedFile(null)}
                />
              </section>

              <section>
                <h2 className="font-display text-sm uppercase tracking-wide text-slate-light mb-3">
                  02 — Job description (optional)
                </h2>
                <JDInput value={jdText} onChange={setJdText} />
              </section>

              {error && (
                <div className="rounded-lg border border-flag/30 bg-flag/5 px-4 py-3">
                  <p className="text-sm text-flag">{error}</p>
                </div>
              )}

              <Button size="lg" onClick={handleAnalyze} disabled={!hasInput}>
                Analyze resume
              </Button>
            </div>
          </div>
        )}

        {appState === "analyzing" && <AnalyzingState />}

        {appState === "results" && result && (
          <div className="space-y-6">
            <DashboardMetrics result={result} />
            <RecruiterEyeViewCard data={result.ai.recruiter_eye_view} />

            {result.mode === "matching" && (
              <div className="rounded-lg border border-signal/30 bg-signal/5 px-4 py-3">
                <p className="text-sm text-paper">
                  <span className="font-medium">Shortlist reasoning: </span>
                  {result.ai.shortlist_reasoning}
                </p>
              </div>
            )}

            <div className="grid md:grid-cols-2 gap-6">
              <HeatMapCard heatMap={result.ai.heat_map} />
              {result.mode === "matching" && <GapAnalysisCard gaps={result.gaps} />}
            </div>

            <StrengthsWeaknesses strengths={result.ai.strengths} weaknesses={result.ai.weaknesses} />
            <LineImprovementsCard items={result.ai.line_improvements} />
            <InterviewReadinessCard data={result.ai.interview_questions} />

            {parsedResume && <ParsedDataPreview resume={parsedResume} />}

            <GrowthTrackerCard />

            <CareerRoadmapCard resumeId={result.resume_id} />

            <p className="text-xs text-slate-light text-center pt-4">
              Analysis used {result.tokens_used.toLocaleString()} AI tokens — scoring and gap
              detection ran on structured data, not your raw resume text.
            </p>
          </div>
        )}
      </main>
    </div>
  );
}
