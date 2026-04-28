"""
═══════════════════════════════════════════════════════════════
Skill Extractor — JobBERT NER-based skill extraction
═══════════════════════════════════════════════════════════════
Uses jjzha/jobbert_skill_extraction (Token Classification)
to extract real skills from resume text. Falls back to
keyword matching if the model is unavailable.
"""

from loguru import logger

from app.config import get_settings
from app.services.hf_client import hf_client, HFClientError
from app.data.skill_categories import categorize_skill, ALL_KNOWN_SKILLS


async def extract_skills_ner(resume_text: str) -> list[dict]:
    """
    Extract skills from resume text using JobBERT NER model.
    
    Returns:
        List of {"name": str, "category": str, "confidence": float}
    """
    settings = get_settings()

    try:
        # JobBERT NER — Token Classification
        # We chunk the text because NER models have token limits (~512)
        chunks = _chunk_text(resume_text, max_chars=1500)
        all_entities: list[dict] = []

        for chunk in chunks:
            result = await hf_client.call(
                settings.model_skill_ner,
                {"inputs": chunk},
            )

            if isinstance(result, list):
                all_entities.extend(result)

        # Process NER output into clean skills
        skills = _process_ner_entities(all_entities)
        logger.info(f"JobBERT extracted {len(skills)} skills via NER")

        # Enrich with keyword-based extraction for any the NER missed
        keyword_skills = _extract_skills_keyword(resume_text)
        ner_names = {s["name"].lower() for s in skills}

        for ks in keyword_skills:
            if ks["name"].lower() not in ner_names:
                ks["confidence"] = max(0.5, ks["confidence"] - 0.1)  # Lower confidence for keyword-only
                skills.append(ks)

        logger.info(f"Total skills after keyword enrichment: {len(skills)}")
        return skills

    except HFClientError as e:
        logger.warning(f"JobBERT NER failed, falling back to keyword extraction: {e}")
        return _extract_skills_keyword(resume_text)


def _chunk_text(text: str, max_chars: int = 1500) -> list[str]:
    """Split text into chunks that fit within model token limits."""
    words = text.split()
    chunks = []
    current_chunk: list[str] = []
    current_len = 0

    for word in words:
        if current_len + len(word) + 1 > max_chars:
            if current_chunk:
                chunks.append(" ".join(current_chunk))
            current_chunk = [word]
            current_len = len(word)
        else:
            current_chunk.append(word)
            current_len += len(word) + 1

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks if chunks else [text[:max_chars]]


def _process_ner_entities(entities: list[dict]) -> list[dict]:
    """
    Process raw NER output into clean, deduplicated skills.
    
    NER output format: [{"entity_group": "Skill", "word": "Python", "score": 0.95}, ...]
    """
    seen: set[str] = set()
    skills: list[dict] = []

    for entity in entities:
        # Handle different NER output formats
        word = entity.get("word", entity.get("entity", "")).strip()
        score = entity.get("score", 0.5)
        entity_group = entity.get("entity_group", entity.get("entity", ""))

        # Skip low-confidence or empty results
        if not word or score < 0.3 or len(word) < 2:
            continue

        # Clean up subword tokens (##ing, etc.)
        word = word.replace("##", "").strip()
        if not word:
            continue

        # Normalize and deduplicate
        normalized = word.lower().strip()
        if normalized in seen:
            continue
        seen.add(normalized)

        # Capitalize properly
        display_name = _normalize_skill_name(word)

        skills.append({
            "name": display_name,
            "category": categorize_skill(display_name),
            "confidence": round(min(score, 1.0), 2),
        })

    # Sort by confidence (highest first)
    skills.sort(key=lambda x: x["confidence"], reverse=True)
    return skills


def _normalize_skill_name(raw: str) -> str:
    """Normalize skill name to proper display format."""
    # Common skill name corrections
    corrections = {
        "javascript": "JavaScript",
        "typescript": "TypeScript",
        "python": "Python",
        "java": "Java",
        "html": "HTML",
        "css": "CSS",
        "sql": "SQL",
        "postgresql": "PostgreSQL",
        "mysql": "MySQL",
        "mongodb": "MongoDB",
        "redis": "Redis",
        "docker": "Docker",
        "kubernetes": "Kubernetes",
        "aws": "AWS",
        "gcp": "GCP",
        "azure": "Azure",
        "git": "Git",
        "github": "GitHub",
        "react": "React",
        "vue": "Vue",
        "angular": "Angular",
        "node.js": "Node.js",
        "nodejs": "Node.js",
        "next.js": "Next.js",
        "nextjs": "Next.js",
        "flutter": "Flutter",
        "dart": "Dart",
        "swift": "Swift",
        "kotlin": "Kotlin",
        "django": "Django",
        "flask": "Flask",
        "fastapi": "FastAPI",
        "express": "Express",
        "spring": "Spring Boot",
        "tensorflow": "TensorFlow",
        "pytorch": "PyTorch",
        "numpy": "NumPy",
        "pandas": "Pandas",
        "scikit-learn": "Scikit-learn",
        "linux": "Linux",
        "nginx": "Nginx",
        "graphql": "GraphQL",
        "rest api": "REST API",
        "ci/cd": "CI/CD",
        "ci cd": "CI/CD",
        "tailwind": "Tailwind CSS",
        "sass": "SASS",
        "redux": "Redux",
        "selenium": "Selenium",
        "jest": "Jest",
        "pytest": "Pytest",
        "c++": "C++",
        "c#": "C#",
        "go": "Go",
        "rust": "Rust",
        "php": "PHP",
        "ruby": "Ruby",
        "scala": "Scala",
        "r": "R",
        "matlab": "MATLAB",
        "nlp": "NLP",
        "ml": "Machine Learning",
        "ai": "AI",
    }

    lower = raw.lower().strip()
    if lower in corrections:
        return corrections[lower]
    
    # Default: title case
    return raw.strip().title() if len(raw) > 3 else raw.strip().upper()


def _extract_skills_keyword(resume_text: str) -> list[dict]:
    """
    Fallback: Extract skills via keyword matching against known skills database.
    Less accurate than NER but always available.
    """
    text_lower = resume_text.lower()
    found: list[dict] = []
    seen: set[str] = set()

    # Check each known skill
    for skill_lower in ALL_KNOWN_SKILLS:
        if skill_lower in seen:
            continue

        # Word boundary check to avoid false positives
        # e.g., "R" shouldn't match "React"
        if len(skill_lower) <= 2:
            # For very short skills (R, Go, C#), require word boundary
            import re
            if re.search(rf"\b{re.escape(skill_lower)}\b", text_lower):
                seen.add(skill_lower)
                name = _normalize_skill_name(skill_lower)
                found.append({
                    "name": name,
                    "category": categorize_skill(name),
                    "confidence": 0.7,
                })
        elif skill_lower in text_lower:
            seen.add(skill_lower)
            name = _normalize_skill_name(skill_lower)
            found.append({
                "name": name,
                "category": categorize_skill(name),
                "confidence": 0.75,
            })

    found.sort(key=lambda x: x["confidence"], reverse=True)
    logger.info(f"Keyword extraction found {len(found)} skills")
    return found
