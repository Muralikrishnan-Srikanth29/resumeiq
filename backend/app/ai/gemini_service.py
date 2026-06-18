"""
Gemini 2.5 Flash client. Sole point of contact with the AI provider.
Receives only compact structured JSON (see ai/prompts.py docstring) —
never raw resume/JD text, never raw PDF bytes. This module is the
enforcement boundary for the "no raw PDF to AI" architectural mandate.
"""
import json
import re

from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential

from app.ai.prompts import (
    ROADMAP_SYSTEM_INSTRUCTION,
    SYSTEM_INSTRUCTION,
    build_evaluation_prompt,
    build_matching_prompt,
    build_roadmap_prompt,
)
from app.ai.schemas import ANALYSIS_RESPONSE_SCHEMA, ROADMAP_RESPONSE_SCHEMA
from app.core.config import get_settings
from app.core.exceptions import AIServiceError
from app.core.logging import get_logger
from app.schemas.analysis import AIAnalysisOutput

logger = get_logger(__name__)

_JSON_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


def _strip_fences(text: str) -> str:
    return _JSON_FENCE_RE.sub("", text).strip()


class GeminiService:
    def __init__(self):
        settings = get_settings()
        self._client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self._model = settings.GEMINI_MODEL
        self._max_output_tokens = settings.GEMINI_MAX_OUTPUT_TOKENS

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
    def _generate(self, system_instruction: str, prompt: str, response_schema) -> tuple[str, int]:
        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.3,
                    max_output_tokens=self._max_output_tokens,
                    response_mime_type="application/json",
                    response_schema=response_schema,
                ),
            )
        except Exception as exc:
            logger.error("Gemini API call failed: %s", exc)
            raise AIServiceError(f"AI provider error: {exc}") from exc

        text = (response.text or "").strip()
        if not text:
            raise AIServiceError("AI provider returned an empty response.")

        tokens_used = 0
        usage = getattr(response, "usage_metadata", None)
        if usage:
            tokens_used = (getattr(usage, "prompt_token_count", 0) or 0) + (
                getattr(usage, "candidates_token_count", 0) or 0
            )
        return text, tokens_used

    def analyze_evaluation(self, resume_summary: dict, rule_output: dict) -> tuple[AIAnalysisOutput, int]:
        prompt = build_evaluation_prompt(resume_summary, rule_output)
        raw, tokens = self._generate(SYSTEM_INSTRUCTION, prompt, ANALYSIS_RESPONSE_SCHEMA)
        return self._parse_analysis(raw), tokens

    def analyze_matching(
        self, resume_summary: dict, jd_summary: dict, rule_output: dict
    ) -> tuple[AIAnalysisOutput, int]:
        prompt = build_matching_prompt(resume_summary, jd_summary, rule_output)
        raw, tokens = self._generate(SYSTEM_INSTRUCTION, prompt, ANALYSIS_RESPONSE_SCHEMA)
        return self._parse_analysis(raw), tokens

    def generate_roadmap(self, resume_summary: dict, current_role: str, target_role: str) -> tuple[dict, int]:
        prompt = build_roadmap_prompt(resume_summary, current_role, target_role)
        raw, tokens = self._generate(ROADMAP_SYSTEM_INSTRUCTION, prompt, ROADMAP_RESPONSE_SCHEMA)
        try:
            return json.loads(_strip_fences(raw)), tokens
        except json.JSONDecodeError as exc:
            logger.error("Failed to parse roadmap JSON: %s | raw=%s", exc, raw[:500])
            raise AIServiceError("AI returned malformed roadmap data.") from exc

    @staticmethod
    def _parse_analysis(raw: str) -> AIAnalysisOutput:
        try:
            data = json.loads(_strip_fences(raw))
            return AIAnalysisOutput.model_validate(data)
        except (json.JSONDecodeError, ValueError) as exc:
            logger.error("Failed to parse AI analysis JSON: %s | raw=%s", exc, raw[:500])
            raise AIServiceError("AI returned malformed analysis data.") from exc


_gemini_service: GeminiService | None = None


def get_gemini_service() -> GeminiService:
    global _gemini_service
    if _gemini_service is None:
        _gemini_service = GeminiService()
    return _gemini_service
