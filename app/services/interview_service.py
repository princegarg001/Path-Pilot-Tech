import json
import re
from loguru import logger
from app.services.hf_client import hf_client
from app.config import get_settings

class InterviewService:
    def __init__(self):
        self._settings = get_settings()
        self.model_id = "mistralai/Mistral-7B-Instruct-v0.2"
        # We can use the text generation model for generating questions

    def _clean_json(self, text: str) -> str:
        """Removes markdown blocks and cleans up text to extract JSON."""
        text = re.sub(r'```json', '', text)
        text = re.sub(r'```', '', text)
        return text.strip()

    async def generate_next_question(self, resume_text: str, history: list, current_question_index: int) -> str:
        """
        Generates the next question based on the resume and the conversation history.
        """
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

        logger.info(f"Generating question #{current_question_index + 1}")
        
        response = await hf_client.call_text_generation(
            model_id=self.model_id,
            prompt=prompt,
            max_new_tokens=250,
            temperature=0.7,
            use_cache=False
        )
        
        question = response.strip()
        # Fallback if it returns empty
        if not question:
            question = "Could you tell me more about your recent experience?"
            
        return question

    async def evaluate_interview(self, resume_text: str, history: list) -> dict:
        """
        Evaluates the entire interview transcript.
        """
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

        logger.info("Evaluating complete interview...")
        
        response = await hf_client.call_text_generation(
            model_id=self.model_id,
            prompt=prompt,
            max_new_tokens=800,
            temperature=0.3, # lower temp for more structured output
            use_cache=False
        )
        
        try:
            cleaned = self._clean_json(response)
            data = json.loads(cleaned)
            return data
        except json.JSONDecodeError:
            logger.error(f"Failed to parse interview evaluation JSON: {response}")
            # Fallback
            return {
                "score": 70,
                "strengths": ["Participated in the interview"],
                "weaknesses": ["Could not parse detailed evaluation"],
                "improvements": ["Try to provide more structured answers next time"]
            }

interview_service = InterviewService()
