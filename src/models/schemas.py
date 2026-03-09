"""Structured output models for judo analysis."""

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


class MomentType(str, Enum):
    GRIP_FIGHT = "grip_fight"
    ATTACK = "attack"
    DEFENSE = "defense"
    GROUNDWORK = "groundwork"
    TRANSITION = "transition"
    STANDING = "standing"
    RESET = "reset"


class TechniqueCategory(str, Enum):
    NAGE_WAZA = "nage_waza"          # Throwing techniques
    KATAME_WAZA = "katame_waza"      # Grappling techniques
    OSAEKOMI_WAZA = "osaekomi_waza"  # Pinning techniques
    SHIME_WAZA = "shime_waza"        # Choking techniques
    KANSETSU_WAZA = "kansetsu_waza"  # Joint lock techniques


class ScoreType(str, Enum):
    IPPON = "ippon"
    WAZA_ARI = "waza_ari"
    NO_SCORE = "no_score"


@dataclass
class TechniqueAnalysis:
    """Detailed analysis of a single judo technique."""
    name: str                        # English name
    japanese_name: str               # Japanese name (e.g., "Seoi Nage")
    category: str                    # TechniqueCategory value
    timestamp_start: float           # seconds
    timestamp_end: float             # seconds
    execution_score: int             # 1-10
    kuzushi_rating: int              # Balance breaking (1-10)
    tsukuri_rating: int              # Entry/fitting (1-10)
    kake_rating: int                 # Execution (1-10)
    score_result: str                # ScoreType value
    biomechanics_notes: str          # Detailed biomechanical observations
    strengths: List[str]             # What was done well
    improvements: List[str]          # Specific actionable improvements
    drill_recommendations: List[str] # Training drills to improve this technique


@dataclass
class MatchMoment:
    """A significant moment detected in the match."""
    timestamp_start: float
    timestamp_end: float
    moment_type: str                 # MomentType value
    description: str
    frame_indices: List[int]         # Which extracted frames correspond


@dataclass
class StrategicInsight:
    """Strategic observation about the player's match approach."""
    category: str                    # e.g., "grip_strategy", "attack_pattern", "defense"
    observation: str
    recommendation: str


@dataclass
class MatchAnalysis:
    """Complete analysis of a judo match."""
    video_filename: str
    duration_sec: float
    total_frames_analyzed: int

    # Detected moments and techniques
    moments: List[MatchMoment]
    techniques: List[TechniqueAnalysis]

    # Overall assessment
    overall_assessment: str
    score_summary: str               # e.g., "Player scored 1 waza-ari, attempted 3 attacks"
    dominant_techniques: List[str]   # Most used techniques
    strengths: List[str]
    weaknesses: List[str]

    # Strategic analysis
    strategic_insights: List[StrategicInsight]

    # Training recommendations
    priority_improvements: List[str]  # Top 3-5 things to work on
    recommended_drills: List[str]     # Specific training exercises
    conditioning_notes: str           # Physical conditioning observations

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        import dataclasses
        return dataclasses.asdict(self)

    def to_text_report(self) -> str:
        """Generate a human-readable text report."""
        lines = []
        lines.append("=" * 60)
        lines.append("JUDO MATCH ANALYSIS REPORT")
        lines.append("=" * 60)
        lines.append(f"\nVideo: {self.video_filename}")
        lines.append(f"Duration: {self.duration_sec:.0f}s | Frames analyzed: {self.total_frames_analyzed}")

        lines.append(f"\n{'─' * 40}")
        lines.append("OVERALL ASSESSMENT")
        lines.append(f"{'─' * 40}")
        lines.append(self.overall_assessment)
        lines.append(f"\nScore summary: {self.score_summary}")

        if self.techniques:
            lines.append(f"\n{'─' * 40}")
            lines.append(f"TECHNIQUES IDENTIFIED ({len(self.techniques)})")
            lines.append(f"{'─' * 40}")
            for i, tech in enumerate(self.techniques, 1):
                lines.append(f"\n  {i}. {tech.japanese_name} ({tech.name})")
                lines.append(f"     Category: {tech.category}")
                lines.append(f"     Time: {tech.timestamp_start:.1f}s - {tech.timestamp_end:.1f}s")
                lines.append(f"     Execution: {tech.execution_score}/10")
                lines.append(f"     Kuzushi: {tech.kuzushi_rating}/10 | Tsukuri: {tech.tsukuri_rating}/10 | Kake: {tech.kake_rating}/10")
                lines.append(f"     Result: {tech.score_result}")
                lines.append(f"     Biomechanics: {tech.biomechanics_notes}")
                if tech.strengths:
                    lines.append(f"     ✓ Strengths: {'; '.join(tech.strengths)}")
                if tech.improvements:
                    lines.append(f"     ✗ Improve: {'; '.join(tech.improvements)}")
                if tech.drill_recommendations:
                    lines.append(f"     🏋 Drills: {'; '.join(tech.drill_recommendations)}")

        lines.append(f"\n{'─' * 40}")
        lines.append("STRENGTHS & WEAKNESSES")
        lines.append(f"{'─' * 40}")
        if self.strengths:
            lines.append("\n  Strengths:")
            for s in self.strengths:
                lines.append(f"    ✓ {s}")
        if self.weaknesses:
            lines.append("\n  Weaknesses:")
            for w in self.weaknesses:
                lines.append(f"    ✗ {w}")

        if self.strategic_insights:
            lines.append(f"\n{'─' * 40}")
            lines.append("STRATEGIC INSIGHTS")
            lines.append(f"{'─' * 40}")
            for insight in self.strategic_insights:
                lines.append(f"\n  [{insight.category}]")
                lines.append(f"    Observation: {insight.observation}")
                lines.append(f"    Recommendation: {insight.recommendation}")

        lines.append(f"\n{'─' * 40}")
        lines.append("TRAINING RECOMMENDATIONS")
        lines.append(f"{'─' * 40}")
        if self.priority_improvements:
            lines.append("\n  Priority improvements:")
            for i, imp in enumerate(self.priority_improvements, 1):
                lines.append(f"    {i}. {imp}")
        if self.recommended_drills:
            lines.append("\n  Recommended drills:")
            for drill in self.recommended_drills:
                lines.append(f"    • {drill}")
        if self.conditioning_notes:
            lines.append(f"\n  Conditioning: {self.conditioning_notes}")

        lines.append(f"\n{'=' * 60}")
        return "\n".join(lines)
