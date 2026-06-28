from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from typing import Any

from groq import Groq
from pydantic import BaseModel, Field


class ReportRequest(BaseModel):
    prompt: str = Field(..., min_length=3, max_length=6000)
    tone: str = Field(default="professional", max_length=60)
    audience: str = Field(default="general audience", max_length=120)


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "report"


def _client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise ValueError("GROQ_API_KEY is not set.")
    return Groq(api_key=api_key)


def _extract_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?", "", cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("Groq did not return JSON.")
    parsed = json.loads(cleaned[start : end + 1])
    if not isinstance(parsed, dict):
        raise ValueError("Groq JSON payload must be an object.")
    return parsed


def _clean_items(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _build_markdown(title: str, generated_at: str, prompt: str, summary: str, findings: list[str], recommendations: list[str], next_steps: list[str]) -> str:
    lines = [
        f"# {title}",
        "",
        f"Generated: {generated_at}",
        "",
        "## Executive Summary",
        summary,
        "",
        "## Key Findings",
    ]
    lines.extend(f"- {item}" for item in findings or ["No key findings were returned."])
    lines.extend(["", "## Recommendations"])
    lines.extend(f"- {item}" for item in recommendations or ["No recommendations were returned."])
    lines.extend(["", "## Action Plan"])
    lines.extend(f"- {item}" for item in next_steps or ["No action plan was returned."])
    lines.extend(["", "## User Prompt", prompt])
    return "\n".join(lines)


def _fallback_report(request: ReportRequest, reason: str) -> dict[str, Any]:
    generated_at = datetime.now(timezone.utc).isoformat()
    title = f"Report for {request.prompt[:50].strip()}".strip()
    summary = (
        "A fallback report was generated because the Groq API was not available. "
        f"Requested topic: {request.prompt.strip()}."
    )
    findings = [
        "The application is wired for chat-style prompt entry.",
        "The backend returns a downloadable Markdown report.",
        f"Fallback reason: {reason}",
    ]
    recommendations = [
        "Set GROQ_API_KEY in your .env file.",
        "Adjust the prompt to match the report you want to create.",
        "Use the download button to save the Markdown file.",
    ]
    next_steps = [
        "Type a prompt in the frontend.",
        "Generate the report.",
        "Download the file and share it.",
    ]
    markdown = _build_markdown(title, generated_at, request.prompt, summary, findings, recommendations, next_steps)
    return {
        "title": title,
        "generated_at": generated_at,
        "prompt": request.prompt,
        "executive_summary": summary,
        "key_findings": findings,
        "recommendations": recommendations,
        "action_plan": next_steps,
        "report_markdown": markdown,
        "download_filename": f"{_slugify(title)}.md",
        "model": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        "status": "fallback",
    }


def build_report(request: ReportRequest) -> dict[str, Any]:
    prompt = request.prompt.strip()
    if not prompt:
        raise ValueError("Prompt is required.")

    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    generated_at = datetime.now(timezone.utc).isoformat()

    try:
        client = _client()
        completion = client.chat.completions.create(
            model=model,
            temperature=0.35,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert report writer. Return JSON only with keys: "
                        "title, executive_summary, key_findings, recommendations, action_plan. "
                        "The array fields must be arrays of strings. Do not wrap the JSON in markdown fences."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Write a {request.tone} report for {request.audience}. "
                        f"Topic: {prompt}. "
                        "Make it concise, polished, and ready for a downloadable report interface."
                    ),
                },
            ],
        )
        content = completion.choices[0].message.content or ""
        parsed = _extract_json(content)
        title = str(parsed.get("title") or f"Report for {prompt[:50]}").strip()
        summary = str(parsed.get("executive_summary") or "No executive summary was returned.").strip()
        findings = _clean_items(parsed.get("key_findings"))
        recommendations = _clean_items(parsed.get("recommendations"))
        next_steps = _clean_items(parsed.get("action_plan"))
        markdown = _build_markdown(title, generated_at, prompt, summary, findings, recommendations, next_steps)
        return {
            "title": title,
            "generated_at": generated_at,
            "prompt": prompt,
            "executive_summary": summary,
            "key_findings": findings,
            "recommendations": recommendations,
            "action_plan": next_steps,
            "report_markdown": markdown,
            "download_filename": f"{_slugify(title)}.md",
            "model": model,
            "status": "success",
        }
    except Exception as exc:
        return _fallback_report(request, str(exc))
