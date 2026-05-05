import json
import re
from loguru import logger
from app.services.hf_client import hf_client, HFClientError
from app.config import get_settings

# Fallback questions when LLM is unavailable
_FALLBACK_QUESTIONS = [
    "Welcome! Could you please introduce yourself and tell me about your most recent role?",
    "What was the most challenging technical problem you solved recently, and how did you approach it?",
    "Can you describe a project where you had to collaborate closely with a team? What was your role?",
    "How do you stay up to date with the latest trends and technologies in your field?",
    "Where do you see yourself professionally in the next 3 to 5 years?",
]

class InterviewService:
    def __init__(self):
        self._settings = get_settings()
        # Use the same model as all other services (from config: Mistral-7B-Instruct-v0.3)

    def _clean_json(self, text: str) -> str:
        """Removes markdown blocks and cleans up text to extract JSON."""
        text = re.sub(r'```json', '', text)
        text = re.sub(r'```', '', text)
        return text.strip()

    async def generate_next_question(self, resume_text: str, history: list, current_question_index: int) -> str:
        """
        Generates the next question based on the resume and the conversation history.
        Falls back to pre-defined questions if the LLM is unavailable.
        """
        model_id = self._settings.model_text_gen

        # Format the history
        formatted_history = ""
        if history:
            for msg in history:
                role = "Candidate" if msg.role == "user" else "Interviewer"
                formatted_history += f"{role}: {msg.content}\n"

        prompt = f"""<s>[INST] You are an expert technical and HR interviewer. 
Your goal is to conduct a professional job interview based on the candidate's resume.
This is question #{current_question_index + 1}.

Candidate's Resume Extract:
{resume_text[:2000]}

Conversation History:
{formatted_history}

Generate the NEXT single question to ask the candidate. 
If this is the first question, start with a welcoming tone and ask them to introduce themselves or talk about a specific project on their resume.
If there is history, follow up on their previous answer or move to a new topic from their resume.
Do NOT output anything else except the exact text of the question. [/INST]"""

        logger.info(f"Generating question #{current_question_index + 1} using model={model_id}")

        try:
            response = await hf_client.call_text_generation(
                model_id=model_id,
                prompt=prompt,
                max_new_tokens=250,
                temperature=0.7,
                use_cache=False
            )

            question = response.strip()
            # Fallback if it returns empty
            if not question:
                raise ValueError("Empty response from LLM")

            return question
        except (HFClientError, ValueError, Exception) as e:
            logger.warning(f"LLM question generation failed, using fallback: {e}")
            # Use a fallback question based on the index
            idx = current_question_index % len(_FALLBACK_QUESTIONS)
            return _FALLBACK_QUESTIONS[idx]

    async def evaluate_interview(self, resume_text: str, history: list) -> dict:
        """
        Evaluates the entire interview transcript.
        Falls back to rule-based evaluation if the LLM is unavailable.
        """
        model_id = self._settings.model_text_gen

        formatted_history = ""
        for msg in history:
            role = "Candidate" if msg.role == "user" else "Interviewer"
            formatted_history += f"{role}: {msg.content}\n"

        prompt = f"""<s>[INST] You are an expert technical interviewer evaluating a candidate based on their interview transcript.

Candidate's Resume Extract:
{resume_text[:2000]}

Interview Transcript:
{formatted_history}

Provide a comprehensive evaluation of the candidate's performance. You MUST return your answer in valid JSON format matching exactly this structure:
{{
  "score": 85, // integer 0-100
  "strengths": ["Clear communication", "Good technical depth in Python"],
  "weaknesses": ["Lacked detail on system design", "Stumbled on behavioral questions"],
  "improvements": ["Practice STAR method", "Review scalable architectures"]
}}
Do NOT wrap the JSON in markdown code blocks. Just output the JSON. [/INST]"""

        logger.info(f"Evaluating complete interview using model={model_id}...")

        try:
            response = await hf_client.call_text_generation(
                model_id=model_id,
                prompt=prompt,
                max_new_tokens=800,
                temperature=0.3,  # lower temp for more structured output
                use_cache=False
            )

            try:
                cleaned = self._clean_json(response)
                data = json.loads(cleaned)
                # Validate required fields
                data.setdefault("score", 70)
                data.setdefault("strengths", ["Participated in the interview"])
                data.setdefault("weaknesses", [])
                data.setdefault("improvements", [])
                return data
            except json.JSONDecodeError:
                logger.error(f"Failed to parse interview evaluation JSON: {response}")
                return self._fallback_evaluation(history)

        except (HFClientError, Exception) as e:
            logger.warning(f"LLM evaluation failed, using fallback: {e}")
            return self._fallback_evaluation(history)

    @staticmethod
    def _fallback_evaluation(history: list) -> dict:
        """Rule-based fallback evaluation when LLM is unavailable."""
        user_answers = [m for m in history if hasattr(m, 'role') and m.role == 'user']
        # Also handle dict-based history
        if not user_answers:
            user_answers = [m for m in history if isinstance(m, dict) and m.get('role') == 'user']

        total_words = 0
        for ans in user_answers:
            content = ans.content if hasattr(ans, 'content') else ans.get('content', '')
            total_words += len(content.split())

        avg_words = total_words / max(len(user_answers), 1)
        answered_count = len(user_answers)

        score = min(100, 40 + (answered_count * 8) + int(avg_words * 0.5))

        strengths = []
        weaknesses = []
        improvements = []

        if answered_count >= 3:
            strengths.append("Completed multiple interview questions")
        if avg_words >= 30:
            strengths.append("Provided detailed responses")
        if avg_words >= 50:
            strengths.append("Demonstrated depth in answers")

        if avg_words < 20:
            weaknesses.append("Answers were too brief — try to elaborate more")
            improvements.append("Use the STAR method (Situation, Task, Action, Result) for behavioral questions")
        if answered_count < 3:
            weaknesses.append("Answered fewer questions than expected")
            improvements.append("Practice answering questions under time pressure")

        if not strengths:
            strengths.append("Participated in the interview")
        if not improvements:
            improvements.append("Practice mock interviews regularly to build confidence")

        return {
            "score": score,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "improvements": improvements,
        }

interview_service = InterviewService()
