"""
═══════════════════════════════════════════════════════════════
Pydantic Schemas — Request/Response models for all endpoints
═══════════════════════════════════════════════════════════════
Every API input and output is strictly validated through these models.
"""

from pydantic import BaseModel, Field
from typing import Optional


# ══════════════════════════════════════════════════════════════
# SHARED / COMMON
# ══════════════════════════════════════════════════════════════

class SkillItem(BaseModel):
    """A single extracted skill with metadata."""
    name: str = Field(..., description="Skill name (e.g., 'Python', 'Docker')")
    category: str = Field(..., description="Category: Frontend, Backend, DevOps, Data, Mobile, Soft Skills, Other")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Extraction confidence (0.0-1.0)")


class GapItem(BaseModel):
    """A single identified skill gap."""
    area: str = Field(..., description="Gap area name (e.g., 'Cloud & DevOps')")
    missing_skills: list[str] = Field(..., description="Specific missing skills")
    priority: str = Field(..., description="Priority: high, medium, low")
    reason: str = Field("", description="Why this gap matters for the target role")


class RecommendationItem(BaseModel):
    """A single actionable recommendation."""
    type: str = Field(..., description="Type: skill, resume, project, networking, certification")
    title: str = Field(..., description="Short recommendation title")
    reason: str = Field(..., description="Why this is recommended")
    resources: list[str] = Field(default_factory=list, description="Free learning resource URLs")


# ══════════════════════════════════════════════════════════════
# /analyze-resume
# ══════════════════════════════════════════════════════════════

class ResumeAnalysisRequest(BaseModel):
    """Input for resume analysis endpoint."""
    resume_text: str = Field(
        ...,
        min_length=50,
        description="Raw resume text (extracted from PDF/TXT on the client side)"
    )
    target_role: Optional[str] = Field(
        None,
        description="Optional target role for gap analysis (e.g., 'Senior Backend Developer')"
    )


class ResumeAnalysisResponse(BaseModel):
    """Full resume analysis output."""
    summary: str = Field(..., description="AI-generated professional resume summary")
    score: int = Field(..., ge=0, le=100, description="Overall resume strength score")
    experience_level: str = Field(..., description="Detected: junior, mid, senior")
    skills: list[SkillItem] = Field(..., description="All extracted skills with categories")
    gaps: list[GapItem] = Field(default_factory=list, description="Identified skill gaps")
    sections_found: list[str] = Field(..., description="Resume sections detected")
    sections_missing: list[str] = Field(default_factory=list, description="Important missing sections")
    recommendations: list[RecommendationItem] = Field(default_factory=list, description="Actionable recommendations")
    keyword_count: int = Field(0, description="Number of strong action verbs/keywords found")


# ══════════════════════════════════════════════════════════════
# /ats-score
# ══════════════════════════════════════════════════════════════

class ATSScoreRequest(BaseModel):
    """Input for ATS scoring endpoint."""
    resume_text: str = Field(..., min_length=50, description="Raw resume text")
    job_description: str = Field(..., min_length=50, description="Job description to match against")


class ATSScoreResponse(BaseModel):
    """ATS compatibility analysis output."""
    overall_score: int = Field(..., ge=0, le=100, description="Combined ATS score")
    semantic_score: int = Field(..., ge=0, le=100, description="Semantic similarity score")
    keyword_score: int = Field(..., ge=0, le=100, description="Keyword match score")
    matched_keywords: list[str] = Field(..., description="Keywords found in both resume and JD")
    missing_keywords: list[str] = Field(..., description="Important JD keywords missing from resume")
    suggestions: list[str] = Field(..., description="Specific improvement suggestions")


# ══════════════════════════════════════════════════════════════
# /generate-plan
# ══════════════════════════════════════════════════════════════

class PlanTaskItem(BaseModel):
    """A single task in the career plan."""
    title: str
    description: str
    category: str = Field(..., description="Resume, Technical, Learning, Portfolio, Networking, Interview, Application")
    estimated_minutes: int = Field(..., ge=10, le=120)
    priority: str = Field("medium", description="high, medium, low")
    addresses_gap: Optional[str] = Field(None, description="Which specific gap this task addresses")


class PlanDayItem(BaseModel):
    """A single day in the 7-day plan."""
    day: int = Field(..., ge=1, le=7)
    theme: str
    tasks: list[PlanTaskItem]


class PlanGenerationRequest(BaseModel):
    """Input for plan generation endpoint."""
    target_role: str = Field(..., description="Target role (e.g., 'Senior Backend Developer')")
    career_goal: str = Field("", description="Specific career goal statement")
    skills: list[str] = Field(..., description="User's current skills")
    gaps: list[GapItem] = Field(default_factory=list, description="Identified skill gaps from analysis")
    experience_level: str = Field("mid", description="junior, mid, senior")
    resume_weaknesses: list[str] = Field(default_factory=list, description="Resume issues to address")


class PlanGenerationResponse(BaseModel):
    """Generated 7-day career plan output."""
    summary: str
    days: list[PlanDayItem]
    total_tasks: int = 0
    total_hours: float = 0.0


# ══════════════════════════════════════════════════════════════
# /generate-questions
# ══════════════════════════════════════════════════════════════

class QuestionItem(BaseModel):
    """A single interview question."""
    question: str
    category: str = Field(..., description="Behavioral, Technical, System Design, Situational")
    difficulty: str = Field(..., description="Easy, Medium, Hard")
    tips: str = Field("", description="Tips for answering this question")


class QuestionGenerationRequest(BaseModel):
    """Input for question generation endpoint."""
    target_role: str = Field(..., description="Target role")
    skills: list[str] = Field(..., description="User's current skills")
    experience_level: str = Field("mid", description="junior, mid, senior")
    count: int = Field(10, ge=5, le=20, description="Number of questions to generate")


class QuestionGenerationResponse(BaseModel):
    """Generated interview questions output."""
    questions: list[QuestionItem]
    total: int = 0


# ══════════════════════════════════════════════════════════════
# /review-task
# ══════════════════════════════════════════════════════════════

class TaskReviewRequest(BaseModel):
    """Input for task review endpoint."""
    task_title: str = Field(..., description="Title of the task being reviewed")
    task_description: str = Field(..., description="Full description of what the task requires")
    task_category: Optional[str] = Field(None, description="Task category (Resume, Technical, etc.)")
    submission_text: str = Field(..., min_length=10, description="User's description of what they did")
    links: list[str] = Field(default_factory=list, description="Optional supporting links")


class TaskReviewResponse(BaseModel):
    """AI-generated task review output."""
    score: int = Field(..., ge=1, le=5, description="Quality score (1-5)")
    passed: bool = Field(..., description="Whether the score is > 3 (task can be marked complete)")
    feedback: str = Field(..., description="Overall assessment of the submission")
    strengths: list[str] = Field(default_factory=list, description="Things done well")
    improvements: list[str] = Field(default_factory=list, description="Areas to improve")


# ══════════════════════════════════════════════════════════════
# /interview (Voice Agent)
# ══════════════════════════════════════════════════════════════

class InterviewMessage(BaseModel):
    role: str = Field(..., description="user or assistant")
    content: str = Field(..., description="The message text")

class InterviewStateRequest(BaseModel):
    resume_text: str = Field(..., description="User's parsed resume text")
    history: list[InterviewMessage] = Field(default_factory=list, description="Conversation history")
    current_question_index: int = Field(0, description="Current question number")

class InterviewEvaluationResponse(BaseModel):
    score: int = Field(..., ge=0, le=100, description="Overall interview performance score")
    strengths: list[str] = Field(default_factory=list, description="What the candidate did well")
    weaknesses: list[str] = Field(default_factory=list, description="Where the candidate is lacking")
    improvements: list[str] = Field(default_factory=list, description="Specific actionable improvements")


# ══════════════════════════════════════════════════════════════
# HEALTH
# ══════════════════════════════════════════════════════════════

class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "ok"
    version: str = "1.0.0"
    models: dict[str, str] = Field(default_factory=dict)
