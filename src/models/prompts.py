"""Prompt templates for LLM interactions."""

from typing import Dict, Any


class PromptTemplates:
    """Templates for LLM prompts."""

    # Video analysis prompt
    VIDEO_ANALYSIS_PROMPT = """
    Analyze the video and provide a summary of:
    1. Video quality metrics
    2. Scene changes detected
    3. Key moments identified

    Video metadata:
    {video_metadata}

    Please provide your analysis in a structured format.
    """

    # Pose analysis prompt
    POSE_ANALYSIS_PROMPT = """
    Based on the pose data below, analyze the athlete's form and provide feedback:

    Pose Data:
    {pose_data}

    Please provide:
    1. Assessment of body alignment
    2. Joint angles analysis
    3. Recommendations for improvement
    """

    # Technique recognition prompt
    TECHNIQUE_RECOGNITION_PROMPT = """
    Based on the following pose data and angles, identify the judo technique:

    Pose Features:
    - Elbow Angles: {elbow_angles}
    - Knee Angles: {knee_angles}
    - Hip Angles: {hip_angles}
    - Torso Tilt: {torso_tilt}

    Possible techniques:
    - Seoi Nage (Shoulder throw)
    - O Soto Gari (Major outer reap)
    - Uchi Mata (Inner thigh throw)
    - Harai Goshi (Sweeping hip throw)

    What technique is being performed? Provide your answer with confidence score.
    """

    # Strategy analysis prompt
    STRATEGY_ANALYSIS_PROMPT = """
    Based on the technique sequence and spacing analysis, provide strategic recommendations:

    Technique Sequence:
    {technique_sequence}

    Spacing Analysis:
    {spacing_analysis}

    Please provide:
    1. Assessment of current strategy
    2. Recommended adjustments
    3. Suggested techniques to counter opponent
    """

    @classmethod
    def get_template(cls, template_name: str) -> str:
        """Get a prompt template by name."""
        templates = {
            "video_analysis": cls.VIDEO_ANALYSIS_PROMPT,
            "pose_analysis": cls.POSE_ANALYSIS_PROMPT,
            "technique_recognition": cls.TECHNIQUE_RECOGNITION_PROMPT,
            "strategy_analysis": cls.STRATEGY_ANALYSIS_PROMPT,
        }
        return templates.get(template_name, "")


def format_prompt(template: str, **kwargs) -> str:
    """
    Format a prompt template with provided arguments.

    Args:
        template: The prompt template string
        **kwargs: Arguments to format the template

    Returns:
        Formatted prompt string
    """
    return template.format(**kwargs)
