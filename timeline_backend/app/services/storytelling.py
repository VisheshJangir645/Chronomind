import json
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class StorytellingService:
    """
    Converts a structured array of discrete historical events into a flowing, 
    educationally-tuned narrative utilizing Generative AI.
    """
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    def generate_narrative(self, 
                           events: List[Dict], 
                           format_type: str = "story", 
                           user_level: str = "intermediate") -> str:
        if not events:
            return "No chronological events provided for narrative generation."

        chronological_string = "\n".join([
            f"- [{e.get('date', 'Unknown')}] {e.get('description', '')} (Actor: {e.get('actor', 'None')})"
            for e in events
        ])

        tone_instruction = self._get_tone_instruction(user_level)
        format_instruction = self._get_format_instruction(format_type)

        system_prompt = (
            f"You are an expert history professor possessing profound narrative skills. "
            f"Your objective is to consume the following strict chronological sequence of facts and synthesize them. "
            f"Rule 1: You must not hallucinate any events or dates not provided in the list. "
            f"Rule 2: {format_instruction} "
            f"Rule 3: {tone_instruction} "
        )

        user_prompt = f"Chronological Data:\n{chronological_string}"

        logger.info(f"Dispatching GenAI request for {format_type} at {user_level} difficulty.")
        
        return self._generate_mock_output(format_type, user_level)

    def _get_tone_instruction(self, level: str) -> str:
        if level == "beginner":
            return "Write at an 8th-grade reading level. Focus heavily on an engaging, story-like flow."
        elif level == "advanced":
            return "Write at a graduate academic level. Focus on socioeconomic causality."
        return "Write clearly and engagingly for a general audience."

    def _get_format_instruction(self, format_type: str) -> str:
        if format_type == "story":
            return "Format the output as a continuous, flowing historical narrative."
        elif format_type == "slides":
            return "Format the output as a presentation deck with ## Slide: headers."
        elif format_type == "summary":
            return "Format the output as a strict 2-paragraph executive summary."
        return ""

    def _generate_mock_output(self, format_type: str, level: str) -> str:
        if format_type == "slides":
            return "## Slide 1: The Outbreak\n- In late 1939...\n- Geographic borders shifted...\n## Slide 2: The Resolution\n- By 1945..."
        return f"This is a mocked output demonstrating the {format_type} pipeline for a {level} user."
