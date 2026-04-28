"""
═══════════════════════════════════════════════════════════════
Plan Router — POST /generate-plan
═══════════════════════════════════════════════════════════════
"""

from fastapi import APIRouter, HTTPException
from loguru import logger

from app.models.schemas import PlanGenerationRequest, PlanGenerationResponse
from app.services.plan_generator import generate_plan

router = APIRouter()


@router.post(
    "/generate-plan",
    response_model=PlanGenerationResponse,
    summary="Generate a personalized 7-day career plan",
    description="Uses Mistral-7B-Instruct to generate a personalized plan "
                "based on skills, gaps, target role, and experience level. "
                "Falls back to intelligent rule-based generation if LLM fails.",
)
async def create_plan(request: PlanGenerationRequest):
    try:
        logger.info(
            f"Generating plan: role={request.target_role}, "
            f"level={request.experience_level}, "
            f"skills={len(request.skills)}, gaps={len(request.gaps)}"
        )

        plan = await generate_plan(request)

        logger.info(f"✓ Plan generated: {plan.total_tasks} tasks, {plan.total_hours}h")
        return plan

    except Exception as e:
        logger.error(f"Plan generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Plan generation failed: {str(e)}")
