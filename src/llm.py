"""LLM client: build the prompt, call DeepSeek, validate the JSON response.

Design notes
------------
- DeepSeek is OpenAI-compatible, so we use the `openai` SDK and just point
  `base_url` at https://api.deepseek.com. Swapping to OpenAI / Together /
  Groq / etc. later is a one-line change.
- We use DeepSeek's native JSON mode (`response_format={"type":"json_object"}`),
  which guarantees syntactically-valid JSON. Pydantic still validates the
  *semantics* (required fields, enum values, etc.) and we retry on failure.
- The client is created lazily so missing API keys fail loudly at call time,
  not at import — keeping unit tests and Streamlit cold-starts clean.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from .models import SplitResult

load_dotenv()

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "story_split.md"
_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)
_DEFAULT_BASE_URL = "https://api.deepseek.com"

_client: Any | None = None


def _get_client() -> Any:
    """Lazily build the OpenAI-compatible client pointed at DeepSeek."""
    global _client
    if _client is None:
        api_key = os.environ.get("DEEPSEEK_API_KEY")
        if not api_key:
            raise RuntimeError(
                "DEEPSEEK_API_KEY is not set. "
                "Add it to .env or your Streamlit Cloud secrets."
            )
        base_url = os.environ.get("DEEPSEEK_BASE_URL", _DEFAULT_BASE_URL)
        from openai import OpenAI

        _client = OpenAI(api_key=api_key, base_url=base_url)
    return _client


def _load_prompt_template() -> str:
    return _PROMPT_PATH.read_text(encoding="utf-8")


def _strip_fences(text: str) -> str:
    """Remove ```json ... ``` fences the model sometimes adds anyway."""
    text = text.strip()
    if text.startswith("```"):
        text = _FENCE_RE.sub("", text).strip()
    return text


def build_prompt(
    raw: str,
    language: str,
    team_context: str,
    tech_stack: str,
    granularity: str,
    template: str | None = None,
) -> str:
    """Render the prompt template with the user-supplied context.

    Exposed separately so it can be unit-tested without touching the API.
    """
    template = template if template is not None else _load_prompt_template()
    schema = SplitResult.model_json_schema()
    return template.format(
        language=language,
        team_context=team_context or "general SaaS team",
        tech_stack=tech_stack or "modern web stack",
        granularity=granularity,
        json_schema=json.dumps(schema, indent=2, ensure_ascii=False),
        raw_requirement=raw.strip(),
    )


def _call_llm(prompt: str, model: str, max_tokens: int) -> str:
    """Thin wrapper around the DeepSeek (OpenAI-compatible) chat API.

    Isolated as a single function so tests can mock just this layer.
    """
    client = _get_client()
    resp = client.chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        # DeepSeek's JSON mode — guarantees the response parses as JSON.
        # The prompt must (and does) mention "JSON" for this to be accepted.
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a Senior Business Analyst. "
                    "You always respond with valid JSON that matches the "
                    "schema embedded in the user prompt. No commentary."
                ),
            },
            {"role": "user", "content": prompt},
        ],
    )
    return resp.choices[0].message.content or ""


def split_requirement(
    raw: str,
    language: str = "English",
    team_context: str = "",
    tech_stack: str = "",
    granularity: str = "Sprint-ready",
    model: str = "deepseek-chat",
    max_retries: int = 2,
    max_tokens: int = 4096,
) -> SplitResult:
    """Split a raw requirement into structured user stories.

    Retries up to `max_retries` extra times if the model returns malformed JSON.
    Raises RuntimeError if all attempts fail; the last validation error and
    last raw response are included for debugging.
    """
    prompt = build_prompt(
        raw=raw,
        language=language,
        team_context=team_context,
        tech_stack=tech_stack,
        granularity=granularity,
    )

    last_err: Exception | None = None
    last_raw: str = ""
    for _ in range(max_retries + 1):
        raw_text = _call_llm(prompt, model=model, max_tokens=max_tokens)
        last_raw = raw_text
        cleaned = _strip_fences(raw_text)
        try:
            return SplitResult.model_validate_json(cleaned)
        except Exception as e:
            last_err = e
            continue

    raise RuntimeError(
        f"LLM output failed validation after {max_retries + 1} attempts: "
        f"{last_err}\n--- raw response ---\n{last_raw[:1000]}"
    )
