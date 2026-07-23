"""
LLM service: turns raw content + a target keyword into a structured gap analysis.

Design note: this mirrors the pattern from Skillbridge — ask the model for
STRICT JSON matching a known schema, then validate it with Pydantic before
it ever reaches the client. If the model returns malformed JSON, we retry
once with a stricter instruction rather than silently failing.
"""

import json
import os
import uuid

from openai import OpenAI

from app.models import AnalyzeResponse, ContentGap

SYSTEM_PROMPT = """You are an SEO content analyst. Given a piece of content and a \
target keyword, identify gaps: subtopics, angles, or details a competitor \
page targeting the same keyword would likely cover but this content doesn't.

Respond with ONLY valid JSON, no markdown fences, matching this exact shape:
{
  "overall_assessment": "one or two sentence summary",
  "gaps": [
    {"topic": "...", "why_it_matters": "...", "priority": "high|medium|low"}
  ],
  "suggested_additions": ["short actionable suggestion", "..."]
}
"""


def _call_openai(content: str, target_keyword: str) -> dict:
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    user_prompt = f"Target keyword: {target_keyword}\n\nContent:\n{content}"

    response = client.chat.completions.create(
        model="gpt-5.6-sol",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)


def _mock_analysis(content: str, target_keyword: str) -> dict:
    """
    Local fallback so this project runs and is demoable without a live API key.
    Same shape the real OpenAI call would return — swap _call_openai in when
    OPENAI_API_KEY is set.
    """
    word_count = len(content.split())
    return {
        "overall_assessment": (
            f"Mock analysis: content is {word_count} words. Set OPENAI_API_KEY "
            f"to run this through GPT-5.6 for a real gap analysis on '{target_keyword}'."
        ),
        "gaps": [
            {
                "topic": "Comparison with alternatives",
                "why_it_matters": "Competing pages for this keyword usually compare options directly.",
                "priority": "medium",
            },
            {
                "topic": "Pricing or cost expectations",
                "why_it_matters": "Buyer-intent keywords tend to rank better with concrete numbers.",
                "priority": "high",
            },
        ],
        "suggested_additions": [
            "Add a short comparison table",
            "Include at least one concrete number or example",
        ],
    }


def analyze_content(content: str, target_keyword: str) -> AnalyzeResponse:
    if os.environ.get("OPENAI_API_KEY"):
        raw = _call_openai(content, target_keyword)
    else:
        raw = _mock_analysis(content, target_keyword)

    return AnalyzeResponse(
        target_keyword=target_keyword,
        overall_assessment=raw["overall_assessment"],
        gaps=[ContentGap(**g) for g in raw["gaps"]],
        suggested_additions=raw["suggested_additions"],
        analysis_id=str(uuid.uuid4()),
    )
