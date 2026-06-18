import {
  AnalyzeResponse,
  HistoryEntry,
  ResumeJSON,
  RoadmapResponse,
} from "./types";
import { getSessionId } from "./session";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const API_V1 = `${API_BASE}/api/v1`;

class APIError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = `Request failed with status ${res.status}`;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      // response body wasn't JSON; keep default message
    }
    throw new APIError(res.status, detail);
  }
  return res.json();
}

export async function uploadResumeFile(
  file: File
): Promise<{ resume_id: string; resume: ResumeJSON }> {
  const formData = new FormData();
  formData.append("session_id", getSessionId());
  formData.append("file", file);

  const res = await fetch(`${API_V1}/resume/upload`, {
    method: "POST",
    body: formData,
  });
  return handleResponse(res);
}

export async function pasteResumeText(
  resumeText: string
): Promise<{ resume_id: string; resume: ResumeJSON }> {
  const formData = new FormData();
  formData.append("session_id", getSessionId());
  formData.append("resume_text", resumeText);

  const res = await fetch(`${API_V1}/resume/paste`, {
    method: "POST",
    body: formData,
  });
  return handleResponse(res);
}

export async function analyze(params: {
  resumeText: string;
  jdText?: string;
}): Promise<AnalyzeResponse> {
  const res = await fetch(`${API_V1}/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: getSessionId(),
      resume_text: params.resumeText,
      jd_text: params.jdText || null,
    }),
  });
  return handleResponse(res);
}

export async function analyzeByResumeId(params: {
  resumeId: string;
  jdText?: string;
}): Promise<AnalyzeResponse> {
  const url = new URL(`${API_V1}/analyze/by-id/${params.resumeId}`);
  url.searchParams.set("session_id", getSessionId());
  if (params.jdText) url.searchParams.set("jd_text", params.jdText);

  const res = await fetch(url.toString(), { method: "POST" });
  return handleResponse(res);
}

export async function generateRoadmap(params: {
  resumeId: string;
  currentRole: string;
  targetRole: string;
}): Promise<RoadmapResponse> {
  const res = await fetch(`${API_V1}/roadmap`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: getSessionId(),
      resume_id: params.resumeId,
      current_role: params.currentRole,
      target_role: params.targetRole,
    }),
  });
  return handleResponse(res);
}

export async function getHistory(
  limit = 20
): Promise<{ history: HistoryEntry[] }> {
  const url = new URL(`${API_V1}/history`);
  url.searchParams.set("session_id", getSessionId());
  url.searchParams.set("limit", String(limit));

  const res = await fetch(url.toString());
  return handleResponse(res);
}

export { APIError };
