export interface ExperienceEntry {
  title: string;
  company: string;
  start_date: string;
  end_date: string;
  duration_months: number;
  bullets: string[];
  raw_block: string;
}

export interface EducationEntry {
  degree: string;
  institution: string;
  year: string;
  gpa: string;
}

export interface ProjectEntry {
  name: string;
  description: string;
  tech_stack: string[];
  link: string;
}

export interface CertificationEntry {
  name: string;
  issuer: string;
  year: string;
}

export interface ResumeJSON {
  name: string;
  email: string;
  phone: string;
  linkedin: string;
  github: string;
  portfolio_url: string;
  experience_years: number;
  skills: string[];
  education: EducationEntry[];
  certifications: CertificationEntry[];
  projects: ProjectEntry[];
  experience: ExperienceEntry[];
  achievements: string[];
  summary_text: string;
  sections_detected: string[];
}

export interface JDJSON {
  required_skills: string[];
  preferred_skills: string[];
  experience_required: number;
  certifications: string[];
  domain: string;
  role_title: string;
  seniority_level: string;
  keywords: string[];
}

export interface RuleEngineScores {
  resume_score: number;
  ats_score: number;
  content_score: number;
  formatting_score: number;
  impact_score: number;
  project_score: number;
  achievements_score: number;
  summary_score: number;
  skills_score: number;
  education_score: number;
}

export interface MatchScores {
  overall_match_score: number;
  skills_match_score: number;
  experience_match_score: number;
  keyword_match_score: number;
  certification_match_score: number;
  ats_match_score: number;
  domain_match_score: number;
}

export interface GapAnalysis {
  exact_skill_matches: string[];
  missing_skills: string[];
  missing_certifications: string[];
  missing_keywords: string[];
  missing_sections: string[];
}

export interface LineImprovement {
  current: string;
  issue: string;
  improved: string;
  reason: string;
}

export interface RecruiterEyeView {
  first_impression: string;
  confidence_score: number;
  rejection_reasons: string[];
  positive_signals: string[];
}

export interface InterviewQuestionSet {
  technical: string[];
  behavioral: string[];
  leadership: string[];
  project_based: string[];
}

export interface AIAnalysisOutput {
  strengths: string[];
  weaknesses: string[];
  recruiter_eye_view: RecruiterEyeView;
  line_improvements: LineImprovement[];
  heat_map: Record<string, number>;
  shortlist_probability: "Low" | "Medium" | "High";
  shortlist_reasoning: string;
  interview_questions: InterviewQuestionSet;
}

export interface AnalyzeResponse {
  analysis_id: string;
  resume_id: string;
  jd_id?: string;
  mode: "evaluation" | "matching";
  scores: RuleEngineScores;
  match_scores: MatchScores | null;
  gaps: GapAnalysis;
  ai: AIAnalysisOutput;
  tokens_used: number;
}

export interface RoadmapResponse {
  roadmap_id: string;
  skill_gaps: string[];
  certification_gaps: string[];
  learning_path: { step: string; resource_type: string; priority: string }[];
  roadmap_90_day: { phase: string; focus_areas: string[]; milestones: string[] }[];
}

export interface HistoryEntry {
  recorded_at: string;
  resume_score: number;
  ats_score: number;
  gap_count: number;
}
