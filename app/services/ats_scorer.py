"""
═══════════════════════════════════════════════════════════════
ATS Scorer — Semantic + Keyword dual-scoring engine
═══════════════════════════════════════════════════════════════
Combines:
  1. Semantic similarity (all-mpnet-base-v2 embeddings + cosine)
  2. Keyword matching (TF-IDF based extraction + overlap)
Final score: 0.6 × semantic + 0.4 × keyword
"""

import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from loguru import logger

from app.config import get_settings
from app.services.hf_client import hf_client, HFClientError


async def calculate_ats_score(
    resume_text: str,
    job_description: str,
) -> dict:
    """
    Full ATS scoring pipeline.
    
    Returns:
        {
            "overall_score": int (0-100),
            "semantic_score": int (0-100),
            "keyword_score": int (0-100),
            "matched_keywords": list[str],
            "missing_keywords": list[str],
            "suggestions": list[str],
        }
    """
    # Run both scoring methods
    semantic_score = await _semantic_score(resume_text, job_description)
    keyword_result = _keyword_score(resume_text, job_description)

    keyword_score = keyword_result["score"]
    matched = keyword_result["matched"]
    missing = keyword_result["missing"]

    # Combined score (semantic weighted higher — catches synonyms)
    overall = int(0.6 * semantic_score + 0.4 * keyword_score)
    overall = max(0, min(100, overall))

    # Generate actionable suggestions
    suggestions = _generate_suggestions(
        overall, semantic_score, keyword_score, missing, resume_text
    )

    logger.info(
        f"ATS Score: overall={overall}, semantic={semantic_score}, "
        f"keyword={keyword_score}, matched={len(matched)}, missing={len(missing)}"
    )

    return {
        "overall_score": overall,
        "semantic_score": semantic_score,
        "keyword_score": keyword_score,
        "matched_keywords": matched,
        "missing_keywords": missing[:15],  # Cap at 15 most important
        "suggestions": suggestions,
    }


async def _semantic_score(resume_text: str, job_description: str) -> int:
    """
    Calculate semantic similarity between resume and JD.
    Uses sentence-transformers/all-mpnet-base-v2 for embeddings.
    """
    settings = get_settings()

    try:
        # Get embeddings for both documents
        result = await hf_client.call(
            settings.model_embeddings,
            {
                "inputs": {
                    "source_sentence": _truncate(job_description, 500),
                    "sentences": [_truncate(resume_text, 500)],
                },
            },
        )

        if isinstance(result, list) and len(result) > 0:
            # Result is similarity scores [0.0 - 1.0]
            similarity = result[0] if isinstance(result[0], (int, float)) else 0.5
            score = int(similarity * 100)
            logger.info(f"Semantic similarity: {score}%")
            return max(0, min(100, score))

        logger.warning("Unexpected embedding response format")
        return 50

    except HFClientError as e:
        logger.warning(f"Semantic scoring failed, using keyword-only: {e}")
        return 50  # Neutral fallback


def _keyword_score(resume_text: str, job_description: str) -> dict:
    """
    TF-IDF based keyword matching between resume and JD.
    
    Returns:
        {"score": int, "matched": list[str], "missing": list[str]}
    """
    # Extract important keywords from JD using TF-IDF
    jd_keywords = _extract_keywords_tfidf(job_description, top_n=30)
    resume_lower = resume_text.lower()

    matched = []
    missing = []

    for keyword in jd_keywords:
        # Check if keyword exists in resume (with word boundary awareness)
        kw_lower = keyword.lower()
        if kw_lower in resume_lower:
            matched.append(keyword)
        else:
            missing.append(keyword)

    # Score based on match ratio
    if not jd_keywords:
        return {"score": 50, "matched": [], "missing": []}

    ratio = len(matched) / len(jd_keywords)
    score = int(ratio * 100)

    return {
        "score": max(0, min(100, score)),
        "matched": matched,
        "missing": missing,
    }


def _extract_keywords_tfidf(text: str, top_n: int = 30) -> list[str]:
    """
    Extract the most important keywords/phrases from text using TF-IDF.
    """
    # Clean the text
    cleaned = re.sub(r"[^\w\s\-\+\#\.\/]", " ", text.lower())
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    if len(cleaned.split()) < 5:
        return []

    try:
        # Use TF-IDF with unigrams and bigrams
        vectorizer = TfidfVectorizer(
            max_features=100,
            stop_words="english",
            ngram_range=(1, 2),
            min_df=1,
            max_df=0.95,
        )
        tfidf_matrix = vectorizer.fit_transform([cleaned])
        feature_names = vectorizer.get_feature_names_out()
        scores = tfidf_matrix.toarray()[0]

        # Sort by TF-IDF score and return top N
        scored = list(zip(feature_names, scores))
        scored.sort(key=lambda x: x[1], reverse=True)

        # Filter out very short or generic terms
        keywords = []
        for word, score in scored:
            if len(word) >= 2 and score > 0.01:
                keywords.append(word.title() if len(word) > 3 else word.upper())
            if len(keywords) >= top_n:
                break

        return keywords

    except Exception as e:
        logger.warning(f"TF-IDF extraction failed: {e}")
        # Fallback: simple word frequency
        words = cleaned.split()
        from collections import Counter
        common = Counter(words).most_common(top_n)
        return [w.title() for w, _ in common if len(w) >= 3]


def _generate_suggestions(
    overall: int,
    semantic: int,
    keyword: int,
    missing_keywords: list[str],
    resume_text: str,
) -> list[str]:
    """Generate actionable improvement suggestions based on scores."""
    suggestions = []

    # Keyword-specific suggestions
    if missing_keywords:
        top_missing = missing_keywords[:5]
        for kw in top_missing:
            suggestions.append(f"Add '{kw}' to your resume — it's a key requirement in the job description")

    # Score-based suggestions
    if keyword < 50:
        suggestions.append(
            "Your resume is missing many keywords from the job description. "
            "Mirror the exact terminology used in the JD."
        )

    if semantic < 60:
        suggestions.append(
            "Your resume's overall focus doesn't closely align with this role. "
            "Rewrite your summary and experience bullets to match the JD's emphasis areas."
        )

    # Resume quality suggestions
    metrics_count = len(re.findall(r"\d+[\+%]|\$\d", resume_text))
    if metrics_count < 3:
        suggestions.append(
            "Add quantifiable achievements (e.g., 'Improved API response time by 40%', "
            "'Managed a team of 8 engineers')."
        )

    if overall >= 80:
        suggestions.append("Your resume is a strong match! Focus on tailoring your cover letter.")
    elif overall >= 60:
        suggestions.append("Good foundation — incorporate the missing keywords and you'll be competitive.")

    return suggestions[:8]  # Cap at 8 suggestions


def _truncate(text: str, max_words: int) -> str:
    """Truncate text to a maximum number of words."""
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words])
