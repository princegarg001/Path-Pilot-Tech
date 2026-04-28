"""
═══════════════════════════════════════════════════════════════
LLM Prompt Templates — All prompts for Mistral-7B-Instruct
═══════════════════════════════════════════════════════════════
Centralized prompt engineering for structured JSON generation.
"""

# ══════════════════════════════════════════════════════════════
# PLAN GENERATION PROMPT
# ══════════════════════════════════════════════════════════════

PLAN_SYSTEM_PROMPT = """You are an expert career coach AI with 20 years of experience in tech recruiting, career development, and interview preparation. You create highly personalized, actionable career improvement plans."""

PLAN_GENERATION_PROMPT = """Create a detailed, personalized 7-day career improvement plan for this candidate.

## CANDIDATE PROFILE
- **Target Role:** {target_role}
- **Career Goal:** {career_goal}
- **Experience Level:** {experience_level}
- **Current Skills:** {skills}
- **High Priority Gaps:** {high_gaps}
- **Medium Priority Gaps:** {medium_gaps}
- **Low Priority Gaps:** {low_gaps}
- **Resume Weaknesses:** {resume_weaknesses}

## ROLE REQUIREMENTS
- **Must Have:** {core_requirements}
- **Preferred:** {preferred_requirements}

## STRICT RULES
1. Each day MUST have exactly 3 tasks (21 tasks total)
2. Tasks must be SPECIFIC and ACTIONABLE — not "learn Docker" but "Complete the Docker Getting Started tutorial (docs.docker.com/get-started) and containerize a simple Python Flask app"
3. Day 1 MUST focus on resume optimization based on the resume weaknesses
4. Days 2-3 MUST address HIGH priority skill gaps with dedicated learning tasks
5. Days 4-5 MUST include portfolio building and interview preparation
6. Day 6 MUST include networking and polishing
7. Day 7 MUST include job applications and a full mock interview
8. Adapt ALL task difficulty to the experience level: {experience_level}
9. Each task must have a realistic time estimate between 15-90 minutes
10. Include specific free resource URLs or platform names where possible

## OUTPUT FORMAT — RESPOND WITH ONLY THIS JSON, NOTHING ELSE:
{{
  "summary": "A 2-3 sentence overview of this personalized plan",
  "days": [
    {{
      "day": 1,
      "theme": "Theme Name",
      "tasks": [
        {{
          "title": "Specific actionable task title",
          "description": "Detailed step-by-step description (2-3 sentences)",
          "category": "Resume",
          "estimated_minutes": 45,
          "priority": "high",
          "addresses_gap": null
        }}
      ]
    }}
  ]
}}

Categories must be one of: Resume, Technical, Learning, Portfolio, Networking, Interview, Application

Generate the complete 7-day plan now. Output ONLY valid JSON."""


# ══════════════════════════════════════════════════════════════
# QUESTION GENERATION PROMPT
# ══════════════════════════════════════════════════════════════

QUESTION_SYSTEM_PROMPT = """You are a senior technical interviewer at a top tech company. You create targeted interview questions based on the candidate's profile to help them prepare effectively."""

QUESTION_GENERATION_PROMPT = """Generate {count} interview questions for a candidate preparing for the role of **{target_role}**.

## CANDIDATE PROFILE
- **Experience Level:** {experience_level}
- **Current Skills:** {skills}

## QUESTION DISTRIBUTION RULES
- 40% Technical questions (related to their skills + role requirements)
- 30% Behavioral questions (STAR method scenarios)
- 20% System Design questions (adapted to their level)
- 10% Situational questions (workplace scenarios)

## DIFFICULTY DISTRIBUTION
- For junior: 40% Easy, 40% Medium, 20% Hard
- For mid: 20% Easy, 50% Medium, 30% Hard
- For senior: 10% Easy, 40% Medium, 50% Hard

## OUTPUT FORMAT — RESPOND WITH ONLY THIS JSON, NOTHING ELSE:
{{
  "questions": [
    {{
      "question": "The full interview question",
      "category": "Technical",
      "difficulty": "Medium",
      "tips": "Key points to mention in your answer"
    }}
  ]
}}

Category must be one of: Technical, Behavioral, System Design, Situational
Difficulty must be one of: Easy, Medium, Hard

Generate exactly {count} questions. Output ONLY valid JSON."""


# ══════════════════════════════════════════════════════════════
# RESUME SUMMARY PROMPT (for BART — shorter, focused)
# ══════════════════════════════════════════════════════════════

SUMMARY_REFINEMENT_PROMPT = """Summarize this resume into a professional 2-3 sentence career summary suitable for the top of a resume. Focus on years of experience, key technical skills, and notable achievements. Be concise and impactful.

Resume:
{resume_text}"""
