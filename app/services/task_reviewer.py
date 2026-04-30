"""
═══════════════════════════════════════════════════════════════
Task Reviewer — AI-powered task submission evaluation
═══════════════════════════════════════════════════════════════
Uses Mistral-7B to evaluate whether a user's task submission
meets the requirements, and returns a score (1-5) with feedback.
"""

import json
import re
from loguru import logger
from app.config import get_settings
from app.services.hf_client import hf_client, HFClientError
from app.models.schemas import TaskReviewRequest, TaskReviewResponse


TASK_REVIEW_PROMPT = """You are a strict but encouraging career coach reviewing a student's task submission.

## TASK DETAILS
- **Title:** {task_title}
- **Description:** {task_description}
- **Category:** {task_category}

## STUDENT'S SUBMISSION
{submission_text}

{links_section}

## SCORING RUBRIC (1-5 scale)
- **1 — Not Started:** No meaningful effort. Submission is blank, irrelevant, or just a copy of the task.
- **2 — Minimal Effort:** Some attempt but clearly incomplete. Missing most requirements.
- **3 — Partial Completion:** Decent effort, covers some requirements but has significant gaps. Not ready yet.
- **4 — Good Work:** Solid effort. Covers main requirements with minor gaps. Demonstrates understanding.
- **5 — Excellent:** Thorough, well-done submission. Goes above expectations. Professional quality.

## RULES
1. Be fair but hold standards — a score of 4+ means the work is genuinely good
2. A score of 3 means "close but not quite" — encourage the student
3. Provide 2-3 specific strengths (things they did well)
4. Provide 1-3 specific improvements (what to do better)
5. The feedback should be encouraging but honest
6. Consider the links provided (if any) as supporting evidence

## OUTPUT FORMAT — RESPOND WITH ONLY THIS JSON, NOTHING ELSE:
{{
  "score": 4,
  "feedback": "A 2-3 sentence overall assessment of the submission quality.",
  "strengths": ["Specific thing done well #1", "Specific thing done well #2"],
  "improvements": ["Specific suggestion #1", "Specific suggestion #2"]
}}

Output ONLY valid JSON. No markdown, no explanations."""


async def review_task(request: TaskReviewRequest) -> TaskReviewResponse:
    """Review a task submission using AI, with rule-based fallback."""
    try:
        result = await _review_with_llm(request)
        if result:
            logger.info(f"✓ AI review complete — score: {result.score}/5")
            return result
        logger.warning("LLM review failed, using rule-based fallback")
    except Exception as e:
        logger.warning(f"LLM review exception: {e}")

    return _rule_based_review(request)


async def _review_with_llm(request: TaskReviewRequest) -> TaskReviewResponse | None:
    """Use Mistral-7B to evaluate the submission."""
    settings = get_settings()

    links_section = ""
    if request.links:
        links_text = "\n".join(f"  - {link}" for link in request.links)
        links_section = f"**Supporting Links:**\n{links_text}"

    prompt = TASK_REVIEW_PROMPT.format(
        task_title=request.task_title,
        task_description=request.task_description,
        task_category=request.task_category or "General",
        submission_text=request.submission_text,
        links_section=links_section,
    )

    raw_text = await hf_client.call_text_generation(
        settings.model_text_gen, prompt,
        max_new_tokens=500, temperature=0.3, use_cache=False,
    )

    if not raw_text:
        return None

    data = _extract_json(raw_text)
    if not data:
        return None

    return _parse_review_json(data)


def _extract_json(text: str) -> dict | None:
    """Extract JSON from LLM output (handles markdown code blocks)."""
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass
    for pattern in [r"```json\s*(.*?)\s*```", r"```\s*(.*?)\s*```", r"\{[\s\S]*\}"]:
        for match in re.findall(pattern, text, re.DOTALL):
            try:
                return json.loads(match.strip())
            except json.JSONDecodeError:
                continue
    return None


def _parse_review_json(data: dict) -> TaskReviewResponse | None:
    """Parse and validate the AI review response."""
    try:
        score = int(data.get("score", 3))
        score = max(1, min(5, score))  # Clamp to 1-5

        return TaskReviewResponse(
            score=score,
            passed=score > 3,
            feedback=data.get("feedback", "Review completed."),
            strengths=data.get("strengths", []),
            improvements=data.get("improvements", []),
        )
    except Exception as e:
        logger.error(f"Review JSON parse failed: {e}")
        return None


def _rule_based_review(request: TaskReviewRequest) -> TaskReviewResponse:
    """Fallback rule-based review when AI is unavailable."""
    text = request.submission_text.strip()
    word_count = len(text.split())
    has_links = bool(request.links)

    # Simple heuristic scoring
    score = 1
    strengths = []
    improvements = []

    if word_count >= 10:
        score = 2
        strengths.append("You've made an effort to describe your work")
    if word_count >= 30:
        score = 3
        strengths.append("Decent level of detail in your description")
    if word_count >= 60:
        score = 4
        strengths.append("Thorough description of your work")
    if word_count >= 100 and has_links:
        score = 5
        strengths.append("Comprehensive submission with supporting evidence")

    if has_links:
        score = min(5, score + 1)
        strengths.append("Included supporting links as evidence")

    if word_count < 30:
        improvements.append("Provide more detail about what you actually did")
    if not has_links:
        improvements.append("Consider adding links to your work (GitHub, docs, etc.)")
    if word_count < 60:
        improvements.append("Describe specific steps you took and results you achieved")

    feedback = (
        f"Your submission has {word_count} words. "
        f"{'Good effort!' if score >= 3 else 'Try to be more detailed about your work.'} "
        f"{'Great that you included supporting links.' if has_links else ''}"
    ).strip()

    return TaskReviewResponse(
        score=score,
        passed=score > 3,
        feedback=feedback,
        strengths=strengths[:3],
        improvements=improvements[:3],
    )
