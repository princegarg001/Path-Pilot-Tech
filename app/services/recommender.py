"""
═══════════════════════════════════════════════════════════════
Recommender — Gap analysis + actionable recommendations
═══════════════════════════════════════════════════════════════
Compares extracted skills against role requirements to identify
gaps and generate prioritized recommendations with resources.
"""

from loguru import logger

from app.data.role_taxonomy import get_role_requirements
from app.data.skill_categories import categorize_skill
from app.data.resources import get_resources_for_skill
from app.models.schemas import GapItem, RecommendationItem


def analyze_gaps(
    extracted_skills: list[dict],
    target_role: str | None = None,
) -> list[GapItem]:
    """
    Identify skill gaps by comparing user skills against role requirements.
    
    Args:
        extracted_skills: [{"name": str, "category": str, "confidence": float}, ...]
        target_role: Target role string for looking up requirements
        
    Returns:
        List of GapItem with priority levels
    """
    if not target_role:
        return _generic_gaps(extracted_skills)

    requirements = get_role_requirements(target_role)
    user_skill_names = {s["name"].lower() for s in extracted_skills}

    gaps: list[GapItem] = []

    # Check core requirements (high priority)
    core_missing = [
        s for s in requirements.get("core", [])
        if not _skill_present(s, user_skill_names)
    ]
    if core_missing:
        # Group by category
        grouped = _group_by_category(core_missing)
        for area, skills in grouped.items():
            gaps.append(GapItem(
                area=area,
                missing_skills=skills,
                priority="high",
                reason=f"Core requirement for {target_role}. These skills are mentioned in 90%+ of job postings.",
            ))

    # Check preferred requirements (medium priority)
    preferred_missing = [
        s for s in requirements.get("preferred", [])
        if not _skill_present(s, user_skill_names)
    ]
    if preferred_missing:
        grouped = _group_by_category(preferred_missing)
        for area, skills in grouped.items():
            gaps.append(GapItem(
                area=area,
                missing_skills=skills,
                priority="medium",
                reason=f"Preferred skill for {target_role}. Having these will make you a stronger candidate.",
            ))

    # Check nice-to-have (low priority)
    nice_missing = [
        s for s in requirements.get("nice_to_have", [])
        if not _skill_present(s, user_skill_names)
    ]
    if nice_missing:
        grouped = _group_by_category(nice_missing)
        for area, skills in grouped.items():
            gaps.append(GapItem(
                area=area,
                missing_skills=skills,
                priority="low",
                reason=f"Nice-to-have for {target_role}. These differentiate senior candidates.",
            ))

    logger.info(f"Found {len(gaps)} gap areas for role '{target_role}'")
    return gaps


def generate_recommendations(
    extracted_skills: list[dict],
    gaps: list[GapItem],
    weaknesses: list[str],
    target_role: str | None = None,
) -> list[RecommendationItem]:
    """
    Generate actionable recommendations based on gaps and weaknesses.
    """
    recommendations: list[RecommendationItem] = []

    # Skill-based recommendations (from gaps)
    for gap in gaps:
        if gap.priority == "high":
            for skill in gap.missing_skills[:3]:  # Top 3 per gap area
                resources = get_resources_for_skill(skill)
                recommendations.append(RecommendationItem(
                    type="skill",
                    title=f"Learn {skill}",
                    reason=f"{skill} is a core requirement for {target_role or 'your target role'}. "
                           f"{gap.reason}",
                    resources=resources[:2],
                ))

    # Resume-based recommendations (from weaknesses)
    weakness_recs = {
        "no_metrics": RecommendationItem(
            type="resume",
            title="Add quantifiable metrics to every bullet point",
            reason="Resumes with numbers get 40% more callbacks. Use the format: 'Improved X by Y% resulting in Z'.",
            resources=["https://www.freecodecamp.org/news/how-to-write-a-resume-that-works/"],
        ),
        "weak_action_verbs": RecommendationItem(
            type="resume",
            title="Strengthen your action verbs",
            reason="Replace weak verbs (worked, helped, did) with power verbs (architected, spearheaded, optimized).",
            resources=[],
        ),
        "missing_summary": RecommendationItem(
            type="resume",
            title="Add a professional summary section",
            reason="A strong 2-3 sentence summary at the top captures recruiter attention in the first 6 seconds.",
            resources=[],
        ),
        "missing_projects": RecommendationItem(
            type="project",
            title="Add a Projects section with 2-3 portfolio projects",
            reason="Portfolio projects demonstrate practical ability and are crucial for roles without extensive work experience.",
            resources=["https://github.com/practical-tutorials/project-based-learning"],
        ),
        "missing_skills": RecommendationItem(
            type="resume",
            title="Add a dedicated Skills/Technologies section",
            reason="ATS systems scan for a skills section. List technologies in categories (Languages, Frameworks, Tools).",
            resources=[],
        ),
        "no_links": RecommendationItem(
            type="resume",
            title="Add GitHub and LinkedIn profile links",
            reason="85% of recruiters check your GitHub/LinkedIn. Include clickable links in your resume header.",
            resources=[],
        ),
        "no_contact_info": RecommendationItem(
            type="resume",
            title="Add complete contact information",
            reason="Include email, phone number, and city/state at minimum. Missing contact info is an instant rejection.",
            resources=[],
        ),
        "too_short": RecommendationItem(
            type="resume",
            title="Expand your resume with more detail",
            reason="Your resume is too brief. Add more context to experience bullets and include all relevant projects.",
            resources=[],
        ),
        "too_long": RecommendationItem(
            type="resume",
            title="Condense your resume to 1-2 pages",
            reason="Most recruiters spend 6-7 seconds on initial scan. Keep it focused on relevant experience only.",
            resources=[],
        ),
        "missing_experience": RecommendationItem(
            type="resume",
            title="Add work experience or internship details",
            reason="Experience section is the most important part. Include internships, freelance work, or open source contributions.",
            resources=[],
        ),
        "missing_education": RecommendationItem(
            type="resume",
            title="Add your education details",
            reason="Include degree, institution, graduation year, and relevant coursework or GPA if strong.",
            resources=[],
        ),
        "missing_certifications": RecommendationItem(
            type="certification",
            title="Consider getting industry certifications",
            reason="Certifications like AWS Cloud Practitioner or Google Associate Cloud Engineer validate your skills objectively.",
            resources=["https://aws.amazon.com/certification/", "https://cloud.google.com/learn/certification"],
        ),
    }

    for weakness in weaknesses:
        if weakness in weakness_recs:
            recommendations.append(weakness_recs[weakness])

    # Networking recommendation (always useful)
    if target_role:
        recommendations.append(RecommendationItem(
            type="networking",
            title=f"Connect with {target_role} professionals on LinkedIn",
            reason="Networking leads to 70% of job placements. Send personalized connection requests mentioning shared interests.",
            resources=["https://www.linkedin.com/"],
        ))

    # Limit to top 10 most impactful
    return recommendations[:10]


def _skill_present(skill: str, user_skills: set[str]) -> bool:
    """Check if a skill (or its common variant) is in the user's skill set."""
    normalized = skill.lower()

    # Direct match
    if normalized in user_skills:
        return True

    # Check for partial matches (e.g., "Python" matches "Python 3")
    for user_skill in user_skills:
        if normalized in user_skill or user_skill in normalized:
            return True

    # Handle OR-type requirements like "Python/Java/Go"
    if "/" in skill:
        alternatives = [s.strip().lower() for s in skill.split("/")]
        return any(alt in user_skills for alt in alternatives)

    return False


def _group_by_category(skills: list[str]) -> dict[str, list[str]]:
    """Group a list of skills by their category."""
    groups: dict[str, list[str]] = {}
    for skill in skills:
        cat = categorize_skill(skill)
        area = cat if cat != "Other" else "General Skills"
        if area not in groups:
            groups[area] = []
        groups[area].append(skill)
    return groups


def _generic_gaps(extracted_skills: list[dict]) -> list[GapItem]:
    """Generate generic gaps when no target role is specified."""
    categories_present = {s["category"] for s in extracted_skills}
    gaps = []

    all_categories = {"Frontend", "Backend", "Database", "DevOps & Cloud", "Tools & Practices"}
    missing_categories = all_categories - categories_present

    for cat in missing_categories:
        gaps.append(GapItem(
            area=cat,
            missing_skills=[],
            priority="medium",
            reason=f"No {cat} skills detected. Consider broadening your skill set.",
        ))

    return gaps
