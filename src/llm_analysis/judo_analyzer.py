from langchain_openai import OpenAI
from langchain_core.prompts import PromptTemplate
import os
import logging
from typing import List, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JudoAnalyzer:
    def __init__(self, api_key: str = None):
        """
        Initialize the Judo Analyzer with OpenAI integration.

        Args:
            api_key: OpenAI API key (optional if set in environment)
        """
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key

        self.llm = OpenAI(temperature=0.7)
        self.prompt_template = PromptTemplate(
            input_variables=["match_description"],
            template="""
            As an expert Judo analyst, review the following sequence from a Judo match and provide:
            1. Identified techniques
            2. Analysis of execution
            3. Suggestions for improvement
            4. Strategic insights
            
            Match sequence:
            {match_description}
            """,
        )

    def _format_sequence(self, captions: List[Dict]) -> str:
        """Format frame captions into a readable sequence."""
        sequence = []
        for caption in captions:
            timestamp = f"Frame {caption['timestamp']}"
            sequence.append(f"{timestamp}: {caption['caption']}")
        return "\n".join(sequence)

    def analyze_sequence(self, captions: List[Dict]) -> str:
        """
        Analyze a sequence of frame captions to provide judo insights.

        Args:
            captions: List of dictionaries containing frame captions and timestamps

        Returns:
            String containing the analysis
        """
        try:
            # Format the sequence
            match_description = self._format_sequence(captions)

            # Generate the prompt
            prompt = self.prompt_template.format(match_description=match_description)

            # Get analysis from LLM
            analysis = self.llm(prompt)

            logger.info("Successfully generated analysis")
            return analysis

        except Exception as e:
            logger.error(f"Error generating analysis: {str(e)}")
            raise
