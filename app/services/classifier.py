"""
═══════════════════════════════════════════════════════════════
Classifier — BART-Large-MNLI zero-shot skill classification
═══════════════════════════════════════════════════════════════
Categorizes extracted skills into domains (Frontend, Backend,
DevOps, etc.) using zero-shot classification when the local
skill_categories lookup doesn't have a match.
"""

from loguru import logger

from app.config import get_settings
from app.services.hf_client import hf_client, HFClientError
from app.data.skill_categories import categorize_skill

# Categories for zero-shot classification
CLASSIFICATION_LABELS = [
    "Frontend Development",
    "Backend Development",
    "Database",
    "DevOps and Cloud",
    "Data Science and AI",
    "Mobile Development",
    "Tools and Practices",
    "Soft Skills",
]

# Map model output back to our category names
LABEL_TO_CATEGORY = {
    "Frontend Development": "Frontend",
    "Backend Development": "Backend",
    "Database": "Database",
    "DevOps and Cloud": "DevOps & Cloud",
    "Data Science and AI": "Data & AI",
    "Mobile Development": "Mobile",
    "Tools and Practices": "Tools & Practices",
    "Soft Skills": "Soft Skills",
}


async def classify_skills(
    skills: list[dict],
) -> list[dict]:
    """
    Enhance skill items with AI-based categorization.
    
    First tries local category lookup. For uncategorized skills,
    uses BART-Large-MNLI zero-shot classification.
    
    Args:
        skills: List of {"name": str, "category": str, "confidence": float}
        
    Returns:
        Same list with updated category fields.
    """
    settings = get_settings()
    uncategorized = [s for s in skills if s["category"] == "Other"]

    if not uncategorized:
        logger.info("All skills categorized locally, skipping zero-shot")
        return skills

    logger.info(f"Classifying {len(uncategorized)} uncategorized skills via BART-MNLI")

    try:
        # Batch classify uncategorized skills
        for skill in uncategorized:
            result = await hf_client.call(
                settings.model_classifier,
                {
                    "inputs": f"The skill '{skill['name']}' is used in",
                    "parameters": {
                        "candidate_labels": CLASSIFICATION_LABELS,
                    },
                },
            )

            if isinstance(result, dict) and "labels" in result:
                top_label = result["labels"][0]
                top_score = result["scores"][0]

                if top_score > 0.3:
                    skill["category"] = LABEL_TO_CATEGORY.get(top_label, "Other")
                    logger.debug(
                        f"Classified '{skill['name']}' → {skill['category']} "
                        f"(confidence: {top_score:.2f})"
                    )

    except HFClientError as e:
        logger.warning(f"Zero-shot classification failed, keeping 'Other' category: {e}")

    return skills


async def classify_single_skill(skill_name: str) -> str:
    """Classify a single skill name into its category."""
    # Try local first
    category = categorize_skill(skill_name)
    if category != "Other":
        return category

    settings = get_settings()
    try:
        result = await hf_client.call(
            settings.model_classifier,
            {
                "inputs": f"The skill '{skill_name}' is used in",
                "parameters": {
                    "candidate_labels": CLASSIFICATION_LABELS,
                },
            },
        )

        if isinstance(result, dict) and "labels" in result:
            top_label = result["labels"][0]
            if result["scores"][0] > 0.3:
                return LABEL_TO_CATEGORY.get(top_label, "Other")

    except HFClientError:
        pass

    return "Other"
