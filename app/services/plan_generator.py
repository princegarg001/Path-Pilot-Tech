"""
═══════════════════════════════════════════════════════════════
Plan Generator — Mistral-7B-Instruct career plan generation
═══════════════════════════════════════════════════════════════
Hybrid: LLM for personalized text + rule-based fallback.
"""

import json
import re
from loguru import logger
from app.config import get_settings
from app.services.hf_client import hf_client, HFClientError
from app.models.schemas import (
    PlanGenerationRequest, PlanGenerationResponse,
    PlanDayItem, PlanTaskItem, GapItem,
)
from app.models.prompts import PLAN_GENERATION_PROMPT
from app.data.role_taxonomy import get_role_requirements
from app.data.resources import get_resources_for_skill


async def generate_plan(request: PlanGenerationRequest) -> PlanGenerationResponse:
    """Generate a personalized 7-day plan. LLM-first, rule-based fallback."""
    try:
        plan = await _generate_with_llm(request)
        if plan and len(plan.days) == 7:
            logger.info("✓ LLM plan validated successfully")
            return plan
        logger.warning("LLM plan invalid, using rule-based fallback")
    except Exception as e:
        logger.warning(f"LLM plan generation failed: {e}")
    return _generate_rule_based_plan(request)


async def _generate_with_llm(request: PlanGenerationRequest) -> PlanGenerationResponse | None:
    settings = get_settings()
    requirements = get_role_requirements(request.target_role)
    high_gaps = [g for g in request.gaps if g.priority == "high"]
    medium_gaps = [g for g in request.gaps if g.priority == "medium"]
    low_gaps = [g for g in request.gaps if g.priority == "low"]

    prompt = PLAN_GENERATION_PROMPT.format(
        target_role=request.target_role,
        career_goal=request.career_goal or f"Become a successful {request.target_role}",
        experience_level=request.experience_level,
        skills=", ".join(request.skills) if request.skills else "Not specified",
        high_gaps=", ".join([f"{g.area} ({', '.join(g.missing_skills)})" for g in high_gaps]) or "None",
        medium_gaps=", ".join([f"{g.area} ({', '.join(g.missing_skills)})" for g in medium_gaps]) or "None",
        low_gaps=", ".join([f"{g.area} ({', '.join(g.missing_skills)})" for g in low_gaps]) or "None",
        resume_weaknesses=", ".join(request.resume_weaknesses) or "None detected",
        core_requirements=", ".join(requirements.get("core", [])),
        preferred_requirements=", ".join(requirements.get("preferred", [])),
    )

    raw_text = await hf_client.call_text_generation(
        settings.model_text_gen, prompt,
        max_new_tokens=3000, temperature=0.7, use_cache=False,
    )
    if not raw_text:
        return None

    data = _extract_json(raw_text)
    if not data:
        return None
    return _parse_plan_json(data)


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


def _parse_plan_json(data: dict) -> PlanGenerationResponse | None:
    try:
        days = []
        for day_data in data.get("days", []):
            tasks = []
            for t in day_data.get("tasks", []):
                tasks.append(PlanTaskItem(
                    title=t.get("title", "Task"),
                    description=t.get("description", ""),
                    category=t.get("category", "Learning"),
                    estimated_minutes=min(120, max(10, t.get("estimated_minutes", 30))),
                    priority=t.get("priority", "medium"),
                    addresses_gap=t.get("addresses_gap"),
                ))
            days.append(PlanDayItem(
                day=day_data.get("day", len(days) + 1),
                theme=day_data.get("theme", f"Day {len(days) + 1}"),
                tasks=tasks,
            ))
        total_tasks = sum(len(d.tasks) for d in days)
        total_min = sum(t.estimated_minutes for d in days for t in d.tasks)
        return PlanGenerationResponse(
            summary=data.get("summary", "Your personalized 7-day career plan."),
            days=days, total_tasks=total_tasks, total_hours=round(total_min / 60, 1),
        )
    except Exception as e:
        logger.error(f"Plan JSON parse failed: {e}")
        return None


def _level_advice(level: str, skill: str) -> str:
    if level == "junior":
        return f"follow a beginner tutorial and build a hello-world project with {skill}."
    elif level == "senior":
        return f"build a production-grade example using {skill} with error handling and tests."
    return f"build a small but functional project using {skill}."


def _generate_rule_based_plan(req: PlanGenerationRequest) -> PlanGenerationResponse:
    """Intelligent rule-based plan using the 8 key parameters."""
    high_gaps = [g for g in req.gaps if g.priority == "high"]
    medium_gaps = [g for g in req.gaps if g.priority == "medium"]
    level = req.experience_level
    target = req.target_role
    days: list[PlanDayItem] = []

    # Day 1: Resume & Profile
    days.append(PlanDayItem(day=1, theme="Resume & Profile Optimization", tasks=[
        PlanTaskItem(title="Optimize your resume format and content",
            description=f"Review your resume against {target} job descriptions. Use the STAR method for each bullet. Add quantifiable metrics to every achievement.",
            category="Resume", estimated_minutes=45, priority="high"),
        PlanTaskItem(title="Write a compelling professional summary",
            description=f"Create a 2-3 sentence summary targeting {target}. Include years of experience, key technologies, and a standout achievement.",
            category="Resume", estimated_minutes=20, priority="high"),
        PlanTaskItem(title="Update LinkedIn and GitHub profiles",
            description=f"Update your LinkedIn headline to target '{target}'. Add a professional GitHub README. Ensure consistency across all profiles.",
            category="Networking", estimated_minutes=30, priority="medium"),
    ]))

    # Day 2: High Priority Gap #1
    if high_gaps:
        gap = high_gaps[0]
        skill = gap.missing_skills[0] if gap.missing_skills else gap.area
        res = get_resources_for_skill(skill)
        res_text = f" Start here: {res[0]}" if res else ""
        days.append(PlanDayItem(day=2, theme=f"Mastering {skill}", tasks=[
            PlanTaskItem(title=f"Deep dive into {skill} fundamentals",
                description=f"{skill} is a core requirement for {target}. Learn the fundamentals.{res_text}",
                category="Learning", estimated_minutes=60, priority="high", addresses_gap=skill),
            PlanTaskItem(title=f"Hands-on practice with {skill}",
                description=f"Build a small project using {skill}. " + _level_advice(level, skill),
                category="Technical", estimated_minutes=60, priority="high", addresses_gap=skill),
            PlanTaskItem(title="Practice coding challenges",
                description=f"Solve 3 {'easy' if level == 'junior' else 'medium'} problems on LeetCode. Focus on arrays and hash maps.",
                category="Technical", estimated_minutes=45, priority="medium"),
        ]))
    else:
        days.append(PlanDayItem(day=2, theme="Technical Skill Building", tasks=[
            PlanTaskItem(title="Deepen your strongest technical skill", description=f"Pick your top skill and build something meaningful with it for your {target} portfolio.", category="Technical", estimated_minutes=60, priority="high"),
            PlanTaskItem(title="Practice coding challenges", description="Solve 3 medium problems on LeetCode/HackerRank.", category="Technical", estimated_minutes=45, priority="medium"),
            PlanTaskItem(title="Study industry best practices", description=f"Read 3 articles about current best practices for {target} roles.", category="Learning", estimated_minutes=20, priority="low"),
        ]))

    # Day 3: High Priority Gap #2 or Project
    if len(high_gaps) > 1:
        gap = high_gaps[1]
        skill = gap.missing_skills[0] if gap.missing_skills else gap.area
        res = get_resources_for_skill(skill)
        res_text = f" Resource: {res[0]}" if res else ""
        days.append(PlanDayItem(day=3, theme=f"Learning {skill} + Project", tasks=[
            PlanTaskItem(title=f"Learn {skill} essentials", description=f"{skill} is key for {target}.{res_text} Complete an intro tutorial.", category="Learning", estimated_minutes=60, priority="high", addresses_gap=skill),
            PlanTaskItem(title="Start your portfolio project", description=f"Begin a project combining your skills with {skill}. This becomes your portfolio centerpiece.", category="Portfolio", estimated_minutes=60, priority="high"),
            PlanTaskItem(title="Study interview patterns", description=f"Research top 5 {target} interview question patterns. Write STAR-method notes for each.", category="Interview", estimated_minutes=30, priority="medium"),
        ]))
    else:
        days.append(PlanDayItem(day=3, theme="Portfolio Project", tasks=[
            PlanTaskItem(title="Start your portfolio project", description=f"Build a project that demonstrates your skills for {target}. Include a proper README and clean code.", category="Portfolio", estimated_minutes=75, priority="high"),
            PlanTaskItem(title="Write technical documentation", description="Create clear README, architecture notes, and setup instructions for your project.", category="Portfolio", estimated_minutes=30, priority="medium"),
            PlanTaskItem(title="Study interview patterns", description=f"Research top {target} interview questions. Prepare STAR stories.", category="Interview", estimated_minutes=30, priority="medium"),
        ]))

    # Day 4: Build & Network
    days.append(PlanDayItem(day=4, theme="Build & Network", tasks=[
        PlanTaskItem(title="Continue and deploy your portfolio project", description="Finalize your project. Deploy to GitHub Pages, Vercel, or Railway. Push clean code to GitHub.", category="Portfolio", estimated_minutes=60, priority="high"),
        PlanTaskItem(title=f"Connect with 5 {target} professionals", description="Send personalized LinkedIn requests. Mention shared interests. Join relevant communities.", category="Networking", estimated_minutes=30, priority="medium"),
        PlanTaskItem(title="Research target companies", description="Identify 5 target companies. Note their tech stack, culture, and open positions. Save JDs for ATS matching.", category="Application", estimated_minutes=30, priority="medium"),
    ]))

    # Day 5: Interview Prep
    tech_desc = "Practice 2 medium + 1 hard coding problems. Explain your approach aloud." if level != "junior" else "Practice 2 easy + 1 medium coding problems. Focus on fundamentals."
    sys_desc = "Study 1 system design problem. Practice drawing architecture diagrams." if level != "junior" else "Review core CS concepts: HTTP, REST, databases, basic data structures."
    days.append(PlanDayItem(day=5, theme="Interview Preparation", tasks=[
        PlanTaskItem(title="Technical interview practice", description=tech_desc, category="Interview", estimated_minutes=60, priority="high"),
        PlanTaskItem(title="Behavioral interview preparation", description="Prepare 5 STAR stories: challenging project, conflict, leadership, failure, and 'why this role'.", category="Interview", estimated_minutes=45, priority="high"),
        PlanTaskItem(title="System design study" if level != "junior" else "Technical concepts review", description=sys_desc, category="Technical", estimated_minutes=45, priority="medium"),
    ]))

    # Day 6: Polish
    day6_tasks = [
        PlanTaskItem(title="Customize resume for top 3 companies", description="Tailor your resume for each target company. Mirror JD keywords. Use ATS scoring to validate.", category="Resume", estimated_minutes=45, priority="high"),
    ]
    if medium_gaps:
        skill = medium_gaps[0].missing_skills[0] if medium_gaps[0].missing_skills else medium_gaps[0].area
        day6_tasks.append(PlanTaskItem(title=f"Quick study: {skill}", description=f"Spend 30 min on {skill} basics. Enough to discuss intelligently in interviews.", category="Learning", estimated_minutes=30, priority="medium", addresses_gap=skill))
    else:
        day6_tasks.append(PlanTaskItem(title="Write a technical blog post", description="Write about a technology you know well. Publish on Dev.to or Medium.", category="Portfolio", estimated_minutes=40, priority="medium"))
    day6_tasks.append(PlanTaskItem(title="Prepare questions for interviewers", description="Draft 5 thoughtful questions about team culture, growth, tech decisions, and workflow.", category="Interview", estimated_minutes=20, priority="medium"))
    days.append(PlanDayItem(day=6, theme="Polish & Finalize", tasks=day6_tasks))

    # Day 7: Launch
    mock_desc = "15 min behavioral + 15 min technical." if level == "junior" else "15 min behavioral + 30 min technical + 15 min system design."
    days.append(PlanDayItem(day=7, theme="Apply & Launch", tasks=[
        PlanTaskItem(title="Submit 3-5 job applications", description=f"Apply to top {target} positions with customized resumes and cover letters.", category="Application", estimated_minutes=60, priority="high"),
        PlanTaskItem(title="Full mock interview simulation", description=f"Complete simulation: {mock_desc} Record yourself and review.", category="Interview", estimated_minutes=60, priority="high"),
        PlanTaskItem(title="Review your week and plan ahead", description="Review all tasks. Note what you learned, what needs work, and plan next steps. Celebrate your progress!", category="Application", estimated_minutes=20, priority="medium"),
    ]))

    total_tasks = sum(len(d.tasks) for d in days)
    total_min = sum(t.estimated_minutes for d in days for t in d.tasks)
    return PlanGenerationResponse(
        summary=f"Your personalized 7-day plan to become a {target}. Based on your {level}-level profile, we've created {total_tasks} actionable tasks totaling {round(total_min / 60, 1)} hours.",
        days=days, total_tasks=total_tasks, total_hours=round(total_min / 60, 1),
    )
