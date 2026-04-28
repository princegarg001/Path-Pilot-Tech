"""
═══════════════════════════════════════════════════════════════
Questions Router — POST /generate-questions
═══════════════════════════════════════════════════════════════
"""

from fastapi import APIRouter, HTTPException
from loguru import logger

from app.models.schemas import QuestionGenerationRequest, QuestionGenerationResponse
from app.services.question_generator import generate_questions

router = APIRouter()


@router.post(
    "/generate-questions",
    response_model=QuestionGenerationResponse,
    summary="Generate role-specific interview questions",
    description="Uses Mistral-7B-Instruct to generate targeted interview questions "
                "based on target role, skills, and experience level.",
)
async def create_questions(request: QuestionGenerationRequest):
    try:
        logger.info(
            f"Generating {request.count} questions: role={request.target_role}, "
            f"level={request.experience_level}"
        )

        result = await generate_questions(request)

        logger.info(f"✓ Generated {result.total} interview questions")
        return result

    except Exception as e:
        logger.error(f"Question generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Question generation failed: {str(e)}")
