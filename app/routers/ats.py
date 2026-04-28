"""
═══════════════════════════════════════════════════════════════
ATS Router — POST /ats-score
═══════════════════════════════════════════════════════════════
"""

from fastapi import APIRouter, HTTPException
from loguru import logger

from app.models.schemas import ATSScoreRequest, ATSScoreResponse
from app.services.ats_scorer import calculate_ats_score

router = APIRouter()


@router.post(
    "/ats-score",
    response_model=ATSScoreResponse,
    summary="Calculate ATS compatibility score",
    description="Dual scoring: semantic similarity (all-mpnet-base-v2) + "
                "TF-IDF keyword matching. Returns overall score with suggestions.",
)
async def ats_score(request: ATSScoreRequest):
    try:
        logger.info(f"ATS scoring: resume={len(request.resume_text)} chars, JD={len(request.job_description)} chars")

        result = await calculate_ats_score(
            request.resume_text.strip(),
            request.job_description.strip(),
        )

        response = ATSScoreResponse(**result)
        logger.info(f"✓ ATS score: {response.overall_score}")
        return response

    except Exception as e:
        logger.error(f"ATS scoring failed: {e}")
        raise HTTPException(status_code=500, detail=f"ATS scoring failed: {str(e)}")
