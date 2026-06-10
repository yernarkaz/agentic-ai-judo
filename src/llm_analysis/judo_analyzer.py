"""
Judo match analyzer using GPT-4o Vision.

Multi-pass analysis:
  Pass 1 — Moment detection: identify key judo moments from frames
  Pass 2 — Technique deep dive: detailed analysis of each identified technique
  Pass 3 — Match summary: overall strategic assessment and training recommendations
"""

import os
import time
import base64
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests
from dotenv import load_dotenv

from src.video_processing.frame_extractor import FrameInfo
from src.models.schemas import (
    MatchAnalysis,
    MatchMoment,
    TechniqueAnalysis,
    StrategicInsight,
)

load_dotenv("config/.env")
load_dotenv(override=False)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ── Prompt Templates ──────────────────────────────────────────────

MOMENT_DETECTION_PROMPT = """You are a judo analyst. Identify key moments from these frames.

For each moment found, return JSON:
{
  "moments": [
    {
      "start_timestamp": 0.0,
      "end_timestamp": 5.0,
      "moment_type": "attack",
      "description": "what is happening",
      "frame_indices": [0, 1, 2]
    }
  ]
}

moment_type must be one of: grip_fight, attack, defense, groundwork, transition, standing, reset
frame_indices are the image numbers (0 = first image, 1 = second, etc.)
Respond with JSON only, no other text."""


TECHNIQUE_ANALYSIS_PROMPT = """You are a world-class judo coach analyzing a judo technique.

Context: moment described as "{moment_description}"
Time range: {start_time}s - {end_time}s

Analyze the technique. Respond ONLY with valid JSON:
{{
  "name": "technique name",
  "japanese_name": "Japanese name",
  "category": "nage_waza",
  "execution_score": 7,
  "kuzushi_rating": 8,
  "tsukuri_rating": 6,
  "kake_rating": 7,
  "score_result": "no_score",
  "biomechanics_notes": "observations",
  "strengths": ["good thing"],
  "improvements": ["fix this"],
  "drill_recommendations": ["drill"]
}}"""


MATCH_SUMMARY_PROMPT = """You are an elite judo coach. Generate a match summary from the data below.

**Detected moments:**
{moments_json}

**Technique analyses:**
{techniques_json}

Respond ONLY with valid JSON:
{{
  "overall_assessment": "summary",
  "score_summary": "scoring summary",
  "dominant_techniques": ["tech1"],
  "strengths": ["s1"],
  "weaknesses": ["w1"],
  "strategic_insights": [{{"category": "grip_strategy", "observation": "...", "recommendation": "..."}}],
  "priority_improvements": ["fix1"],
  "recommended_drills": ["drill1"],
  "conditioning_notes": "notes"
}}"""


class JudoAnalyzer:
    def __init__(self, model: str = None, base_url: str = None):
        """
        Initialize the Judo Analyzer with Ollama (local qwen2.5vl).

        Args:
            model: Ollama model name (defaults to OLLAMA_MODEL env var or qwen2.5vl:7b)
            base_url: Ollama base URL (defaults to OLLAMA_BASE_URL env var)
        """
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")).rstrip("/")
        self.model = model or os.getenv("OLLAMA_MODEL", "qwen2.5vl:7b")
        logger.info(f"JudoAnalyzer initialized with Ollama model: {self.model} @ {self.base_url}")

    def _encode_image(self, image_path: str, max_dim: int = 512) -> str:
        """Encode image to base64, resized to reduce VRAM usage."""
        from PIL import Image
        import io

        img = Image.open(image_path)
        if max(img.size) > max_dim:
            img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=70)
        return base64.b64encode(buf.getvalue()).decode("utf-8")

    def _build_vision_messages(
        self, system_prompt: str, frames: List[FrameInfo], user_text: str = ""
    ) -> List[Dict]:
        """Build messages with images for Ollama Vision API."""
        # Ollama expects: content as text, images as separate base64 array
        text_parts = []
        images = []

        if user_text:
            text_parts.append(user_text)

        for i, frame in enumerate(frames):
            text_parts.append(f"[Image {i} - Frame at {frame.timestamp_sec:.1f}s]")
            images.append(self._encode_image(frame.path))

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "\n".join(text_parts), "images": images},
        ]

    def _call_vision(
        self, messages: List[Dict], max_tokens: int = 2000, max_retries: int = 5
    ) -> str:
        """Call Ollama chat API with exponential backoff retry."""
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": self.model,
                        "messages": messages,
                        "options": {
                            "num_predict": max_tokens,
                            "temperature": 0.3,
                        },
                        "stream": False,
                    },
                    timeout=300,
                )
                response.raise_for_status()
                return response.json()["message"]["content"]
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    wait = min(2 ** attempt * 5, 300)
                    logger.warning(f"Request failed: {e} (attempt {attempt+1}/{max_retries}). Retrying in {wait}s...")
                    time.sleep(wait)
                else:
                    raise
        raise RuntimeError(f"Ollama API failed after {max_retries} retries")

    def _parse_json_response(self, text: str, expected_key: str = "moments") -> Dict:
        """Extract and parse JSON from the model response. Handles truncated/ malformed output."""
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
            text = text.strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {e}")
            # Try to find JSON object in the text
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    return json.loads(text[start:end])
                except json.JSONDecodeError:
                    pass
            # Last resort: salvage partial JSON by finding the key and truncating to last complete entry
            key_pos = text.find(f'"{expected_key}"')
            if key_pos >= 0:
                brace_start = text.find("[", max(0, key_pos - 30))
                if brace_start < 0:
                    brace_start = text.find("{", max(0, key_pos - 30))
                if brace_start >= 0:
                    # Find all complete JSON objects/arrays up to last balanced "}"
                    # Walk backwards from end, finding last complete object
                    for end_pos in range(len(text), brace_start + 200, -1):
                        candidate = text[brace_start:end_pos].strip()
                        if candidate.endswith("}"):
                            # Fix trailing commas before closing braces
                            import re
                            candidate = re.sub(r',\s*([}\]])', r'\1', candidate)
                            try:
                                return json.loads(candidate)
                            except json.JSONDecodeError:
                                continue
            raise ValueError(f"Could not parse JSON from model response: {text[:200]}")

    # ── Pass 1: Moment Detection ──────────────────────────────────

    def detect_moments(self, frames: List[FrameInfo]) -> List[MatchMoment]:
        """
        Pass 1: Analyze all frames to identify key judo moments.

        Sends frames in batches to handle large numbers.
        """
        logger.info(f"Pass 1: Detecting moments from {len(frames)} frames...")

        # Send frames in small batches - qwen2.5vl handles ~5 images max per request
        batch_size = 5
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

            response_text = self._call_vision(messages, max_tokens=4096)
            data = self._parse_json_response(response_text)
            # Model may return list directly instead of {"moments": [...]}
            if isinstance(data, list):
                moments_list = data
            else:
                moments_list = data.get("moments", [])

            for m in moments_list:
                if not isinstance(m, dict):
                    continue
                try:
                    moment = MatchMoment(
                        timestamp_start=m.get("start_timestamp", 0),
                        timestamp_end=m.get("end_timestamp", 0),
                        moment_type=m.get("moment_type", "standing"),
                        description=m.get("description", ""),
                        frame_indices=[idx + i for idx in m.get("frame_indices", [])],
                    )
                    all_moments.append(moment)
                except (TypeError, KeyError):
                    logger.warning(f"  Skipping malformed moment: {m}")
                    continue

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
            if isinstance(data, list):
                data = data[0] if data else {}

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

        # Truncate to avoid context overflow — keep only essential fields
        moments_summary = [
            {"ts": m.timestamp_start, "type": m.moment_type, "desc": m.description[:100]}
            for m in moments
        ]
        # Limit to top 15 techniques to fit context window
        tech_summary = []
        for t in techniques[:15]:
            tech_summary.append({
                "name": t.name, "jp": t.japanese_name, "cat": t.category,
                "exec": t.execution_score, "kuzushi": t.kuzushi_rating,
                "result": t.score_result,
                "strengths": t.strengths[:2], "improvements": t.improvements[:2],
            })

        prompt = MATCH_SUMMARY_PROMPT.format(
            moments_json=json.dumps(moments_summary, indent=2),
            techniques_json=json.dumps(tech_summary, indent=2),
        )

        # Use retry wrapper instead of raw requests
        messages = [
            {"role": "system", "content": "You are an elite judo coach."},
            {"role": "user", "content": prompt},
        ]
        response_text = self._call_vision(messages, max_tokens=2000, max_retries=5)
        data = self._parse_json_response(response_text)

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
