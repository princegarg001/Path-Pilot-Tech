"""
═══════════════════════════════════════════════════════════════
Task Review Router — POST /review-task endpoint
═══════════════════════════════════════════════════════════════
AI-powered review of task submissions with scoring.
"""

from fastapi import APIRouter, HTTPException
from loguru import logger

from app.models.schemas import TaskReviewRequest, TaskReviewResponse
from app.services.task_reviewer import review_task

router = APIRouter()


@router.post(
    "/review-task",
    response_model=TaskReviewResponse,
    summary="Review a task submission",
    description=(
        "Evaluate a user's task submission using AI (Mistral-7B). "
        "Returns a score (1-5), feedback, strengths, and improvements. "
        "A score > 3 means the task is considered 'passed'."
    ),
)
async def review_task_endpoint(request: TaskReviewRequest) -> TaskReviewResponse:
    """Review a task submission and return AI-generated score + feedback."""
    logger.info(
        f"📝 [REVIEW] Reviewing submission for task: {request.task_title[:50]}..."
    )

    try:
        result = await review_task(request)
        logger.info(
            f"✅ [REVIEW] Score: {result.score}/5 | "
            f"Passed: {result.passed} | "
            f"Strengths: {len(result.strengths)} | "
            f"Improvements: {len(result.improvements)}"
        )
        return result
    except Exception as e:
        logger.error(f"❌ [REVIEW] Failed: {e}")
        raise HTTPException(status_code=500, detail=f"Review failed: {str(e)}")
