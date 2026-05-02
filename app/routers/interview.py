from fastapi import APIRouter, HTTPException, Body
from loguru import logger
from app.models.schemas import InterviewStateRequest, InterviewEvaluationResponse, InterviewMessage
from app.services.interview_service import interview_service

router = APIRouter(prefix="/interview", tags=["Interview Agent"])

@router.post("/next", response_model=dict, summary="Get next interview question")
async def get_next_question(req: InterviewStateRequest):
    """
    Analyzes the interview history and the user's resume to generate the next question.
    """
    try:
        question = await interview_service.generate_next_question(
            resume_text=req.resume_text,
            history=req.history,
            current_question_index=req.current_question_index
        )
        return {"question": question}
    except Exception as e:
        logger.error(f"Error generating next question: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate next question")


@router.post("/evaluate", response_model=InterviewEvaluationResponse, summary="Evaluate completed interview")
async def evaluate_interview(req: InterviewStateRequest):
    """
    Evaluates the full interview transcript and returns a structured feedback response.
    """
    try:
        evaluation = await interview_service.evaluate_interview(
            resume_text=req.resume_text,
            history=req.history
        )
        return InterviewEvaluationResponse(**evaluation)
    except Exception as e:
        logger.error(f"Error evaluating interview: {e}")
        raise HTTPException(status_code=500, detail="Failed to evaluate interview")
