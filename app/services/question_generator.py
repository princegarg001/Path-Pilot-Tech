"""
═══════════════════════════════════════════════════════════════
Question Generator — Mistral-7B interview question generation
═══════════════════════════════════════════════════════════════
"""

import json
import re
from loguru import logger
from app.config import get_settings
from app.services.hf_client import hf_client, HFClientError
from app.models.schemas import (
    QuestionGenerationRequest,
    QuestionGenerationResponse,
    QuestionItem,
)
from app.models.prompts import QUESTION_GENERATION_PROMPT


async def generate_questions(request: QuestionGenerationRequest) -> QuestionGenerationResponse:
    """Generate role-specific interview questions. Falls back to rule-based."""
    try:
        result = await _generate_with_llm(request)
        if result and len(result.questions) >= 5:
            logger.info(f"✓ LLM generated {len(result.questions)} questions")
            return result
    except Exception as e:
        logger.warning(f"LLM question generation failed: {e}")

    return _generate_rule_based(request)


async def _generate_with_llm(request: QuestionGenerationRequest) -> QuestionGenerationResponse | None:
    settings = get_settings()
    prompt = QUESTION_GENERATION_PROMPT.format(
        count=request.count,
        target_role=request.target_role,
        experience_level=request.experience_level,
        skills=", ".join(request.skills) if request.skills else "General",
    )

    raw = await hf_client.call_text_generation(
        settings.model_text_gen, prompt, max_new_tokens=2000, temperature=0.8, use_cache=False,
    )
    if not raw:
        return None

    data = _extract_json(raw)
    if not data or "questions" not in data:
        return None

    questions = []
    for q in data["questions"]:
        questions.append(QuestionItem(
            question=q.get("question", ""),
            category=q.get("category", "Technical"),
            difficulty=q.get("difficulty", "Medium"),
            tips=q.get("tips", ""),
        ))

    return QuestionGenerationResponse(questions=questions, total=len(questions))


def _extract_json(text: str) -> dict | None:
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


def _generate_rule_based(request: QuestionGenerationRequest) -> QuestionGenerationResponse:
    """Comprehensive rule-based fallback with role-specific questions."""
    level = request.experience_level
    role = request.target_role
    skills = request.skills

    questions: list[QuestionItem] = []

    # Behavioral (always included)
    behavioral = [
        QuestionItem(question="Tell me about a challenging project you worked on and how you overcame obstacles.",
                     category="Behavioral", difficulty="Medium", tips="Use STAR method. Focus on YOUR specific contributions."),
        QuestionItem(question="Describe a time you disagreed with a team member. How did you resolve it?",
                     category="Behavioral", difficulty="Medium", tips="Show empathy and collaboration. Focus on the resolution."),
        QuestionItem(question="Tell me about a time you failed. What did you learn?",
                     category="Behavioral", difficulty="Medium", tips="Be honest. Focus on the learning and how you grew."),
        QuestionItem(question=f"Why do you want to work as a {role}?",
                     category="Behavioral", difficulty="Easy", tips=f"Connect your skills and passion to the {role} position."),
    ]

    # Technical (based on skills)
    technical = []
    for skill in skills[:5]:
        if skill.lower() in ("python", "java", "javascript", "go", "c++"):
            technical.append(QuestionItem(
                question=f"What are the key features of {skill} that make it suitable for your projects?",
                category="Technical", difficulty="Easy" if level == "junior" else "Medium",
                tips=f"Discuss {skill}'s strengths, ecosystem, and your specific use cases.",
            ))
        elif skill.lower() in ("docker", "kubernetes", "aws", "ci/cd"):
            technical.append(QuestionItem(
                question=f"Explain how you have used {skill} in a production environment.",
                category="Technical", difficulty="Medium" if level == "junior" else "Hard",
                tips=f"Describe a real scenario. Mention challenges and how you solved them.",
            ))
        elif skill.lower() in ("react", "vue", "angular", "flutter"):
            technical.append(QuestionItem(
                question=f"How do you manage state in a large {skill} application?",
                category="Technical", difficulty="Medium",
                tips="Discuss state management patterns, trade-offs, and your preferred approach.",
            ))
        else:
            technical.append(QuestionItem(
                question=f"How have you applied {skill} in your work? Give a specific example.",
                category="Technical", difficulty="Medium",
                tips=f"Be specific about the project, your role, and the outcome.",
            ))

    # System Design
    system_design = [
        QuestionItem(
            question="How would you design a URL shortening service like bit.ly?",
            category="System Design",
            difficulty="Hard" if level == "junior" else "Medium",
            tips="Discuss: API design, database schema, hashing, caching, and scalability.",
        ),
        QuestionItem(
            question="Design a real-time notification system for a mobile app.",
            category="System Design",
            difficulty="Hard",
            tips="Cover: push notifications, WebSockets, message queues, and delivery guarantees.",
        ),
    ]

    # Situational
    situational = [
        QuestionItem(
            question="Your production system goes down at 3 AM. Walk me through your response.",
            category="Situational", difficulty="Medium",
            tips="Show methodical approach: assess, communicate, debug, fix, post-mortem.",
        ),
    ]

    # Combine and trim to requested count
    all_q = behavioral + technical + system_design + situational
    questions = all_q[:request.count]

    return QuestionGenerationResponse(questions=questions, total=len(questions))
