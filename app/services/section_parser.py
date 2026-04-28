"""
═══════════════════════════════════════════════════════════════
Section Parser — Resume section detection via heuristics
═══════════════════════════════════════════════════════════════
Splits raw resume text into labeled sections (Education,
Experience, Skills, Projects, etc.) using pattern matching.
This runs locally — no AI model needed.
"""

import re
from loguru import logger


# Section header patterns (case-insensitive)
SECTION_PATTERNS: dict[str, list[str]] = {
    "summary": [
        r"(?:professional\s+)?summary",
        r"(?:career\s+)?objective",
        r"about\s+me",
        r"profile",
        r"overview",
    ],
    "experience": [
        r"(?:work\s+)?experience",
        r"employment\s+history",
        r"work\s+history",
        r"professional\s+experience",
        r"career\s+history",
        r"internship(?:s)?",
    ],
    "education": [
        r"education",
        r"academic\s+(?:background|qualifications?)",
        r"qualifications?",
        r"degrees?",
    ],
    "skills": [
        r"(?:technical\s+)?skills",
        r"technologies",
        r"tech\s+stack",
        r"competenc(?:ies|e)",
        r"proficienc(?:ies|y)",
        r"tools?\s*(?:&|and)?\s*technologies",
        r"areas?\s+of\s+expertise",
    ],
    "projects": [
        r"projects?",
        r"portfolio",
        r"(?:personal|side|key)\s+projects?",
        r"notable\s+(?:work|projects?)",
    ],
    "certifications": [
        r"certifications?",
        r"licenses?\s*(?:&|and)?\s*certifications?",
        r"professional\s+development",
        r"courses?\s+(?:&|and)?\s*certifications?",
    ],
    "achievements": [
        r"achievements?",
        r"awards?\s*(?:&|and)?\s*(?:honors?|achievements?)",
        r"honors?",
        r"recognitions?",
    ],
    "publications": [
        r"publications?",
        r"research(?:\s+papers?)?",
        r"papers?",
    ],
    "languages": [
        r"languages?",
        r"language\s+proficiency",
    ],
    "interests": [
        r"interests?",
        r"hobbies?",
        r"extracurricular",
    ],
    "references": [
        r"references?",
    ],
}

# All important sections that a resume should ideally have
IMPORTANT_SECTIONS = {"summary", "experience", "education", "skills", "projects"}


def parse_sections(resume_text: str) -> dict[str, str]:
    """
    Parse resume text into labeled sections.
    
    Returns:
        Dict mapping section name to its text content.
        Always includes a 'full_text' key with the complete resume.
    """
    sections: dict[str, str] = {"full_text": resume_text}
    lines = resume_text.split("\n")

    # Find section boundaries
    section_starts: list[tuple[int, str]] = []

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or len(stripped) > 80:
            # Skip empty lines and very long lines (likely content, not headers)
            continue

        # Check if this line matches a section header
        for section_name, patterns in SECTION_PATTERNS.items():
            for pattern in patterns:
                # Match lines that are primarily a section header
                # (possibly with some decoration like dashes, colons, etc.)
                if re.match(
                    rf"^[\s\-_=*#|]*{pattern}[\s\-_=*#|:]*$",
                    stripped,
                    re.IGNORECASE,
                ):
                    section_starts.append((i, section_name))
                    break
            else:
                continue
            break

    # Extract text between section boundaries
    for idx, (line_num, section_name) in enumerate(section_starts):
        start = line_num + 1
        end = section_starts[idx + 1][0] if idx + 1 < len(section_starts) else len(lines)
        content = "\n".join(lines[start:end]).strip()
        if content:
            sections[section_name] = content

    # If no sections detected, try to infer from content
    if len(sections) <= 1:
        logger.warning("No section headers detected — treating entire text as unstructured")
        sections["unstructured"] = resume_text

    logger.info(f"Parsed {len(sections) - 1} sections: {[k for k in sections if k != 'full_text']}")
    return sections


def get_found_sections(sections: dict[str, str]) -> list[str]:
    """Get list of section names that were found (excluding 'full_text')."""
    return [k for k in sections.keys() if k not in ("full_text", "unstructured")]


def get_missing_sections(sections: dict[str, str]) -> list[str]:
    """Get list of important sections that are missing from the resume."""
    found = set(sections.keys())
    return [s for s in IMPORTANT_SECTIONS if s not in found]


def detect_resume_weaknesses(resume_text: str, sections: dict[str, str]) -> list[str]:
    """
    Analyze the resume for common weaknesses.
    Returns a list of weakness identifiers.
    """
    weaknesses: list[str] = []

    # Check for missing important sections
    missing = get_missing_sections(sections)
    for section in missing:
        weaknesses.append(f"missing_{section}")

    # Check for quantifiable metrics
    metrics_pattern = r"\d+[\+%]|\$\d|increased|decreased|improved|reduced|generated|saved"
    metrics_count = len(re.findall(metrics_pattern, resume_text, re.IGNORECASE))
    if metrics_count < 3:
        weaknesses.append("no_metrics")

    # Check for action verbs
    action_verbs = [
        "developed", "implemented", "designed", "built", "led", "managed",
        "created", "optimized", "architected", "deployed", "automated",
        "launched", "delivered", "improved", "reduced", "increased",
        "mentored", "collaborated", "spearheaded", "orchestrated",
    ]
    verb_count = sum(1 for v in action_verbs if v in resume_text.lower())
    if verb_count < 3:
        weaknesses.append("weak_action_verbs")

    # Check resume length
    word_count = len(resume_text.split())
    if word_count < 150:
        weaknesses.append("too_short")
    elif word_count > 1500:
        weaknesses.append("too_long")

    # Check for contact info
    has_email = bool(re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", resume_text))
    has_phone = bool(re.search(r"[\+]?[\d\s\-\(\)]{10,}", resume_text))
    if not has_email and not has_phone:
        weaknesses.append("no_contact_info")

    # Check for links (GitHub, LinkedIn, portfolio)
    has_links = bool(re.search(r"https?://|github\.com|linkedin\.com", resume_text, re.IGNORECASE))
    if not has_links:
        weaknesses.append("no_links")

    logger.info(f"Detected {len(weaknesses)} resume weaknesses: {weaknesses}")
    return weaknesses


def detect_experience_level(resume_text: str, skill_count: int) -> str:
    """
    Infer experience level from resume content.
    
    Uses:
    - Years of experience mentions
    - Number of skills extracted
    - Seniority keywords
    """
    text_lower = resume_text.lower()

    # Extract years of experience
    years_patterns = [
        r"(\d+)\+?\s*years?\s+(?:of\s+)?(?:experience|exp)",
        r"(?:experience|exp)\s*:?\s*(\d+)\+?\s*years?",
        r"(\d+)\+?\s*years?\s+(?:in|of|working)",
    ]
    max_years = 0
    for pattern in years_patterns:
        matches = re.findall(pattern, text_lower)
        for m in matches:
            max_years = max(max_years, int(m))

    # Check for seniority keywords
    senior_keywords = ["senior", "lead", "principal", "staff", "architect", "director", "head of", "vp"]
    junior_keywords = ["intern", "fresher", "entry level", "entry-level", "graduate", "student", "trainee"]

    has_senior = any(kw in text_lower for kw in senior_keywords)
    has_junior = any(kw in text_lower for kw in junior_keywords)

    # Decision logic
    if max_years >= 5 or has_senior or skill_count >= 15:
        return "senior"
    elif max_years >= 2 or skill_count >= 8:
        return "mid"
    elif has_junior or max_years < 2:
        return "junior"
    else:
        return "mid"  # default
