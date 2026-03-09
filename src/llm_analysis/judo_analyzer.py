"""
Judo match analyzer using GPT-4o Vision.

Multi-pass analysis:
  Pass 1 — Moment detection: identify key judo moments from frames
  Pass 2 — Technique deep dive: detailed analysis of each identified technique
  Pass 3 — Match summary: overall strategic assessment and training recommendations
"""

import os
import base64
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv

from src.video_processing.frame_extractor import FrameInfo
from src.models.schemas import (
    MatchAnalysis,
    MatchMoment,
    TechniqueAnalysis,
    StrategicInsight,
)

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ── Prompt Templates ──────────────────────────────────────────────

MOMENT_DETECTION_PROMPT = """You are an expert judo analyst with deep knowledge of competitive judo.

You are analyzing frames extracted from a judo match video. Each frame is labeled with its timestamp.

Analyze all the frames and identify the KEY MOMENTS in this match. Focus on:
1. **Grip fighting** (kumi-kata) — when athletes are establishing or fighting for grips
2. **Attack attempts** — any throwing or takedown attempts
3. **Defensive actions** — sprawls, blocks, counters
4. **Groundwork** (ne-waza) — any time the athletes go to the ground
5. **Transitions** — standing to ground or vice versa
6. **Resets** — when the referee stops and restarts the action

For each key moment, provide:
- start_timestamp and end_timestamp (in seconds, from the frame labels)
- moment_type: one of "grip_fight", "attack", "defense", "groundwork", "transition", "standing", "reset"
- description: what is happening in this moment
- frame_indices: which frame numbers (0-indexed) correspond to this moment

Respond ONLY with valid JSON in this exact format:
{
  "moments": [
    {
      "start_timestamp": 0.0,
      "end_timestamp": 5.0,
      "moment_type": "grip_fight",
      "description": "Both athletes are fighting for right-hand collar grip",
      "frame_indices": [0, 1, 2]
    }
  ]
}"""


TECHNIQUE_ANALYSIS_PROMPT = """You are a world-class judo coach and biomechanics expert analyzing a judo technique.

Context: This sequence of frames shows a specific judo moment described as: "{moment_description}"
Time range: {start_time}s - {end_time}s

Analyze the technique shown in these frames with extreme detail. Provide:

1. **Technique identification**: Name the technique (both English and Japanese). Classify it (nage_waza, katame_waza, osaekomi_waza, shime_waza, kansetsu_waza).

2. **Execution ratings** (1-10 scale):
   - kuzushi_rating: How well was balance broken?
   - tsukuri_rating: How well was the entry/fitting?
   - kake_rating: How well was the throw/technique executed?
   - execution_score: Overall execution quality

3. **Score assessment**: Would this score ippon, waza_ari, or no_score under current IJF rules? Why?

4. **Biomechanics**: Detailed observations about body positioning, hip placement, foot placement, grip positions, weight distribution, and posture.

5. **Strengths**: What was done well (list specific items)

6. **Improvements**: Specific, actionable corrections the athlete should make (list specific items)

7. **Drill recommendations**: Training drills that would help improve this specific technique

If the frames do NOT show a clear judo technique (e.g., just standing, walking, or the camera angle is bad), set the technique name to "No clear technique" and provide minimal ratings.

Respond ONLY with valid JSON:
{
  "name": "Shoulder Throw",
  "japanese_name": "Seoi Nage",
  "category": "nage_waza",
  "execution_score": 7,
  "kuzushi_rating": 8,
  "tsukuri_rating": 6,
  "kake_rating": 7,
  "score_result": "waza_ari",
  "biomechanics_notes": "Good hip entry but...",
  "strengths": ["Strong initial pull", "Good timing"],
  "improvements": ["Lower hip position needed", "Keep pulling hand active"],
  "drill_recommendations": ["Band-assisted seoi nage entries", "Hip rotation drills"]
}"""


MATCH_SUMMARY_PROMPT = """You are an elite judo coach preparing a post-match analysis report for a professional judo athlete.

You have the following data from analyzing the match:

**Detected moments:**
{moments_json}

**Technique analyses:**
{techniques_json}

Based on this data, provide a comprehensive match summary with:

1. **overall_assessment**: A 3-5 sentence narrative summary of the match performance
2. **score_summary**: Summary of scoring (e.g., "Player scored 1 waza-ari from seoi nage, attempted 3 attacks total")
3. **dominant_techniques**: List of the player's most used/effective techniques
4. **strengths**: Top strengths demonstrated in this match
5. **weaknesses**: Key weaknesses observed
6. **strategic_insights**: List of strategic observations, each with:
   - category (e.g., "grip_strategy", "attack_pattern", "defense", "conditioning", "timing")
   - observation: what was noticed
   - recommendation: what to change
7. **priority_improvements**: Top 3-5 most important things to work on (ranked)
8. **recommended_drills**: Specific training drills and exercises
9. **conditioning_notes**: Physical conditioning observations and recommendations

Respond ONLY with valid JSON:
{
  "overall_assessment": "...",
  "score_summary": "...",
  "dominant_techniques": ["Seoi Nage", "Osoto Gari"],
  "strengths": ["..."],
  "weaknesses": ["..."],
  "strategic_insights": [
    {"category": "grip_strategy", "observation": "...", "recommendation": "..."}
  ],
  "priority_improvements": ["..."],
  "recommended_drills": ["..."],
  "conditioning_notes": "..."
}"""


class JudoAnalyzer:
    def __init__(self, api_key: str = None, model: str = None):
        """
        Initialize the Judo Analyzer with GPT-4o Vision.

        Args:
            api_key: OpenAI API key (uses env var if not provided)
            model: Model name (defaults to GPT_MODEL env var or gpt-4o)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key required. Set OPENAI_API_KEY in .env or pass api_key."
            )

        self.model = model or os.getenv("GPT_MODEL", "gpt-4o")
        self.client = OpenAI(api_key=self.api_key)
        logger.info(f"JudoAnalyzer initialized with model: {self.model}")

    def _encode_image(self, image_path: str) -> str:
        """Encode image to base64 for the Vision API."""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def _build_vision_messages(
        self, system_prompt: str, frames: List[FrameInfo], user_text: str = ""
    ) -> List[Dict]:
        """Build messages with images for the Vision API."""
        content = []

        if user_text:
            content.append({"type": "text", "text": user_text})

        for frame in frames:
            b64 = self._encode_image(frame.path)
            content.append({"type": "text", "text": f"[Frame at {frame.timestamp_sec}s]"})
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{b64}",
                    "detail": "high",
                },
            })

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content},
        ]

    def _call_vision(
        self, messages: List[Dict], max_tokens: int = 2000
    ) -> str:
        """Call the GPT-4o Vision API and return the text response."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.3,  # Lower temperature for more consistent analysis
        )
        return response.choices[0].message.content

    def _parse_json_response(self, text: str) -> Dict:
        """Extract and parse JSON from the model response."""
        # Try to find JSON in the response (handle markdown code blocks)
        text = text.strip()
        if text.startswith("```"):
            # Remove markdown code block
            lines = text.split("\n")
            text = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
            text = text.strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {e}")
            logger.debug(f"Raw response: {text[:500]}")
            # Try to find JSON object in the text
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    return json.loads(text[start:end])
                except json.JSONDecodeError:
                    pass
            raise ValueError(f"Could not parse JSON from model response: {text[:200]}")

    # ── Pass 1: Moment Detection ──────────────────────────────────

    def detect_moments(self, frames: List[FrameInfo]) -> List[MatchMoment]:
        """
        Pass 1: Analyze all frames to identify key judo moments.

        Sends frames in batches to handle large numbers.
        """
        logger.info(f"Pass 1: Detecting moments from {len(frames)} frames...")

        # Send frames in batches of ~15 to avoid token limits
        batch_size = 15
        all_moments = []

        for i in range(0, len(frames), batch_size):
            batch = frames[i : i + batch_size]
            batch_label = f"Frames {i}-{i + len(batch) - 1}"
            logger.info(f"  Analyzing batch: {batch_label}")

            messages = self._build_vision_messages(
                MOMENT_DETECTION_PROMPT,
                batch,
                f"Analyzing {batch_label} of the match.",
            )

            response_text = self._call_vision(messages, max_tokens=2000)
            data = self._parse_json_response(response_text)

            for m in data.get("moments", []):
                moment = MatchMoment(
                    timestamp_start=m["start_timestamp"],
                    timestamp_end=m["end_timestamp"],
                    moment_type=m["moment_type"],
                    description=m["description"],
                    frame_indices=[idx + i for idx in m.get("frame_indices", [])],
                )
                all_moments.append(moment)

        logger.info(f"  Detected {len(all_moments)} moments")
        return all_moments

    # ── Pass 2: Technique Deep Dive ───────────────────────────────

    def analyze_techniques(
        self, frames: List[FrameInfo], moments: List[MatchMoment]
    ) -> List[TechniqueAnalysis]:
        """
        Pass 2: For each attack/defense moment, do a detailed technique analysis.
        """
        attack_moments = [
            m for m in moments if m.moment_type in ("attack", "defense", "groundwork")
        ]

        if not attack_moments:
            logger.info("Pass 2: No attack moments to analyze in detail")
            return []

        logger.info(f"Pass 2: Deep analysis of {len(attack_moments)} technique moments...")
        techniques = []

        for moment in attack_moments:
            # Get the relevant frames for this moment
            relevant_frames = [
                f for idx, f in enumerate(frames) if idx in moment.frame_indices
            ]

            if not relevant_frames:
                # Fall back to frames near the moment timestamps
                relevant_frames = [
                    f
                    for f in frames
                    if moment.timestamp_start <= f.timestamp_sec <= moment.timestamp_end
                ]

            if not relevant_frames:
                logger.warning(f"  No frames found for moment at {moment.timestamp_start}s")
                continue

            # Limit frames per technique analysis
            if len(relevant_frames) > 8:
                step = len(relevant_frames) // 8
                relevant_frames = relevant_frames[::step][:8]

            prompt = TECHNIQUE_ANALYSIS_PROMPT.format(
                moment_description=moment.description,
                start_time=moment.timestamp_start,
                end_time=moment.timestamp_end,
            )

            messages = self._build_vision_messages(prompt, relevant_frames)
            response_text = self._call_vision(messages, max_tokens=1500)
            data = self._parse_json_response(response_text)

            tech = TechniqueAnalysis(
                name=data.get("name", "Unknown"),
                japanese_name=data.get("japanese_name", "Unknown"),
                category=data.get("category", "nage_waza"),
                timestamp_start=moment.timestamp_start,
                timestamp_end=moment.timestamp_end,
                execution_score=data.get("execution_score", 5),
                kuzushi_rating=data.get("kuzushi_rating", 5),
                tsukuri_rating=data.get("tsukuri_rating", 5),
                kake_rating=data.get("kake_rating", 5),
                score_result=data.get("score_result", "no_score"),
                biomechanics_notes=data.get("biomechanics_notes", ""),
                strengths=data.get("strengths", []),
                improvements=data.get("improvements", []),
                drill_recommendations=data.get("drill_recommendations", []),
            )
            techniques.append(tech)
            logger.info(f"  Analyzed: {tech.japanese_name} ({tech.name})")

        return techniques

    # ── Pass 3: Match Summary ─────────────────────────────────────

    def generate_match_summary(
        self,
        video_filename: str,
        duration_sec: float,
        total_frames: int,
        moments: List[MatchMoment],
        techniques: List[TechniqueAnalysis],
    ) -> MatchAnalysis:
        """
        Pass 3: Generate overall match summary and training recommendations.
        """
        logger.info("Pass 3: Generating match summary and training recommendations...")

        import dataclasses

        moments_data = [dataclasses.asdict(m) for m in moments]
        techniques_data = [dataclasses.asdict(t) for t in techniques]

        prompt = MATCH_SUMMARY_PROMPT.format(
            moments_json=json.dumps(moments_data, indent=2),
            techniques_json=json.dumps(techniques_data, indent=2),
        )

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an elite judo coach."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=2000,
            temperature=0.4,
        )

        data = self._parse_json_response(response.choices[0].message.content)

        # Build strategic insights
        insights = []
        for si in data.get("strategic_insights", []):
            insights.append(
                StrategicInsight(
                    category=si.get("category", "general"),
                    observation=si.get("observation", ""),
                    recommendation=si.get("recommendation", ""),
                )
            )

        analysis = MatchAnalysis(
            video_filename=video_filename,
            duration_sec=duration_sec,
            total_frames_analyzed=total_frames,
            moments=moments,
            techniques=techniques,
            overall_assessment=data.get("overall_assessment", ""),
            score_summary=data.get("score_summary", ""),
            dominant_techniques=data.get("dominant_techniques", []),
            strengths=data.get("strengths", []),
            weaknesses=data.get("weaknesses", []),
            strategic_insights=insights,
            priority_improvements=data.get("priority_improvements", []),
            recommended_drills=data.get("recommended_drills", []),
            conditioning_notes=data.get("conditioning_notes", ""),
        )

        logger.info("  Match summary generated successfully")
        return analysis

    # ── Full Analysis Pipeline ────────────────────────────────────

    def analyze_match(
        self,
        frames: List[FrameInfo],
        video_filename: str,
        duration_sec: float,
    ) -> MatchAnalysis:
        """
        Run the complete 3-pass analysis on a set of extracted frames.

        Args:
            frames: List of FrameInfo from the frame extractor
            video_filename: Name of the source video file
            duration_sec: Video duration in seconds

        Returns:
            Complete MatchAnalysis with all results
        """
        logger.info(f"Starting full analysis of {video_filename}...")

        # Pass 1
        moments = self.detect_moments(frames)

        # Pass 2
        techniques = self.analyze_techniques(frames, moments)

        # Pass 3
        analysis = self.generate_match_summary(
            video_filename=video_filename,
            duration_sec=duration_sec,
            total_frames=len(frames),
            moments=moments,
            techniques=techniques,
        )

        logger.info(
            f"Analysis complete: {len(moments)} moments, "
            f"{len(techniques)} techniques analyzed"
        )
        return analysis
