"""
═══════════════════════════════════════════════════════════════
Summarizer — BART-Large-CNN resume summarization
═══════════════════════════════════════════════════════════════
Generates a professional 2-3 sentence career summary from
the full resume text using facebook/bart-large-cnn.
"""

from loguru import logger

from app.config import get_settings
from app.services.hf_client import hf_client, HFClientError


async def summarize_resume(resume_text: str) -> str:
    """
    Generate a professional summary of the resume.
    
    Uses BART-Large-CNN (summarization model) to create a
    concise 2-3 sentence career summary.
    
    Falls back to a simple extractive summary on failure.
    """
    settings = get_settings()

    # Truncate input to model's max (BART handles ~1024 tokens)
    truncated = resume_text[:3000]

    try:
        result = await hf_client.call(
            settings.model_summarizer,
            {
                "inputs": truncated,
                "parameters": {
                    "max_length": 150,
                    "min_length": 40,
                    "do_sample": False,
                    "num_beams": 4,
                },
            },
        )

        if isinstance(result, list) and len(result) > 0:
            summary = result[0].get("summary_text", "")
            if summary:
                logger.info(f"BART generated summary ({len(summary)} chars)")
                return summary.strip()

        logger.warning("BART returned empty summary, using fallback")
        return _fallback_summary(resume_text)

    except HFClientError as e:
        logger.warning(f"Summarization failed, using fallback: {e}")
        return _fallback_summary(resume_text)


def _fallback_summary(resume_text: str) -> str:
    """
    Simple extractive fallback when BART is unavailable.
    Takes the first few meaningful sentences from the resume.
    """
    import re

    # Try to find an existing summary/objective section
    summary_patterns = [
        r"(?:summary|objective|profile|about\s+me)[:\s]*\n(.+?)(?:\n\n|\n[A-Z])",
        r"^(.+?)(?:\n\n)",
    ]
    for pattern in summary_patterns:
        match = re.search(pattern, resume_text, re.IGNORECASE | re.DOTALL)
        if match:
            text = match.group(1).strip()
            if 30 < len(text) < 500:
                return text

    # Last resort: first 200 chars
    sentences = resume_text.split(".")
    summary_parts = []
    total = 0
    for s in sentences:
        s = s.strip()
        if s and len(s) > 15:
            summary_parts.append(s)
            total += len(s)
            if total > 200 or len(summary_parts) >= 3:
                break

    return ". ".join(summary_parts) + "." if summary_parts else "Professional with diverse experience."
