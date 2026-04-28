"""
═══════════════════════════════════════════════════════════════
Resume Router — POST /analyze-resume
═══════════════════════════════════════════════════════════════
The main analysis pipeline. Chains multiple AI models.
"""

import asyncio
from fastapi import APIRouter, HTTPException
from loguru import logger

from app.models.schemas import (
    ResumeAnalysisRequest,
    ResumeAnalysisResponse,
    SkillItem,
)
from app.services.section_parser import (
    parse_sections,
    get_found_sections,
    get_missing_sections,
    detect_resume_weaknesses,
    detect_experience_level,
)
from app.services.skill_extractor import extract_skills_ner
from app.services.summarizer import summarize_resume
from app.services.classifier import classify_skills
from app.services.recommender import analyze_gaps, generate_recommendations

router = APIRouter()


@router.post(
    "/analyze-resume",
    response_model=ResumeAnalysisResponse,
    summary="Analyze a resume using AI",
    description="Multi-stage AI pipeline: section parsing → NER skill extraction → "
                "summarization → classification → gap analysis → recommendations.",
)
async def analyze_resume(request: ResumeAnalysisRequest):
    """
    Full resume analysis pipeline.
    
    Stages:
    1. Section Detection (local regex)
    2. Skill Extraction (JobBERT NER) + Summarization (BART) — parallel
    3. Skill Classification (BART-MNLI zero-shot)
    4. Gap Analysis + Recommendations (local logic)
    5. Score Calculation
    """
    try:
        resume_text = request.resume_text.strip()
        logger.info(f"Analyzing resume ({len(resume_text)} chars), target: {request.target_role}")

        # Stage 1: Section Detection (local, instant)
        sections = parse_sections(resume_text)
        found_sections = get_found_sections(sections)
        missing_sections = get_missing_sections(sections)

        # Stage 2: Parallel — Skill Extraction + Summarization
        skills_task = asyncio.create_task(extract_skills_ner(resume_text))
        summary_task = asyncio.create_task(summarize_resume(resume_text))

        raw_skills, summary = await asyncio.gather(skills_task, summary_task)

        # Stage 3: Classify uncategorized skills
        classified_skills = await classify_skills(raw_skills)

        # Stage 4: Detect experience level & weaknesses
        experience_level = detect_experience_level(resume_text, len(classified_skills))
        weaknesses = detect_resume_weaknesses(resume_text, sections)

        # Stage 5: Gap analysis
        gaps = analyze_gaps(classified_skills, request.target_role)

        # Stage 6: Recommendations
        recommendations = generate_recommendations(
            classified_skills, gaps, weaknesses, request.target_role
        )

        # Stage 7: Calculate score
        score = _calculate_score(
            classified_skills, found_sections, missing_sections,
            weaknesses, gaps, resume_text
        )

        # Build response
        skill_items = [
            SkillItem(name=s["name"], category=s["category"], confidence=s["confidence"])
            for s in classified_skills
        ]

        response = ResumeAnalysisResponse(
            summary=summary,
            score=score,
            experience_level=experience_level,
            skills=skill_items,
            gaps=gaps,
            sections_found=found_sections,
            sections_missing=missing_sections,
            recommendations=recommendations,
            keyword_count=len(classified_skills),
        )

        logger.info(
            f"✓ Analysis complete: score={score}, skills={len(skill_items)}, "
            f"gaps={len(gaps)}, level={experience_level}"
        )
        return response

    except Exception as e:
        logger.error(f"Resume analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


def _calculate_score(
    skills: list[dict],
    found_sections: list[str],
    missing_sections: list[str],
    weaknesses: list[str],
    gaps: list,
    resume_text: str,
) -> int:
    """
    Calculate resume strength score (0-100).
    
    Formula:
    - Skills score (35%): based on count and quality
    - Sections score (15%): completeness
    - Weakness penalty (20%): deductions for issues
    - Experience depth (20%): content quality signals
    - Gap penalty (10%): high-priority gaps reduce score
    """
    # Skills score (0-35)
    skill_count = len(skills)
    if skill_count >= 15:
        skills_score = 35
    elif skill_count >= 10:
        skills_score = 30
    elif skill_count >= 5:
        skills_score = 22
    elif skill_count >= 3:
        skills_score = 15
    else:
        skills_score = 8

    # Sections score (0-15)
    total_important = len(found_sections) + len(missing_sections)
    sections_score = int((len(found_sections) / max(total_important, 1)) * 15)

    # Weakness penalty (0-20, lower is worse)
    weakness_penalty = max(0, 20 - len(weaknesses) * 3)

    # Experience depth (0-20)
    import re
    metrics_count = len(re.findall(r"\d+[\+%]|\$\d", resume_text))
    action_verbs = ["developed", "implemented", "designed", "built", "led", "managed",
                    "created", "optimized", "deployed", "automated", "launched"]
    verb_count = sum(1 for v in action_verbs if v in resume_text.lower())
    experience_score = min(20, (metrics_count * 3) + (verb_count * 2))

    # Gap penalty (0-10, lower gaps = higher score)
    high_gaps = sum(1 for g in gaps if g.priority == "high")
    gap_score = max(0, 10 - high_gaps * 3)

    total = skills_score + sections_score + weakness_penalty + experience_score + gap_score
    return max(10, min(100, total))
