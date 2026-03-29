"""Data models for analysis results."""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class FrameData:
    """Data for a single video frame."""

    frame_number: int
    timestamp: float
    width: int
    height: int
    frame: str  # base64 encoded image

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "frame_number": self.frame_number,
            "timestamp": self.timestamp,
            "width": self.width,
            "height": self.height,
            "frame": self.frame,
        }


@dataclass
class PoseData:
    """Data for a detected pose."""

    frame_number: int
    timestamp: float
    num_landmarks: int
    landmarks: List[Dict[str, Any]]
    angles: Dict[str, float]
    bbox: Dict[str, int]
    confidence: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "frame_number": self.frame_number,
            "timestamp": self.timestamp,
            "num_landmarks": self.num_landmarks,
            "landmarks": self.landmarks,
            "angles": self.angles,
            "bbox": self.bbox,
            "confidence": self.confidence,
        }


@dataclass
class TechniqueData:
    """Data for a recognized technique."""

    technique: str
    category: str
    confidence: float
    matched_features: Dict[str, Any]
    matches: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "technique": self.technique,
            "category": self.category,
            "confidence": self.confidence,
            "matched_features": self.matched_features,
            "matches": self.matches,
        }


@dataclass
class AnalysisResult:
    """Complete analysis result."""

    video_source: str
    analysis_type: str
    timestamp: str
    frames: List[FrameData] = field(default_factory=list)
    poses: List[PoseData] = field(default_factory=list)
    techniques: List[TechniqueData] = field(default_factory=list)
    synthesis: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "video_source": self.video_source,
            "analysis_type": self.analysis_type,
            "timestamp": self.timestamp,
            "frames": [f.to_dict() for f in self.frames],
            "poses": [p.to_dict() for p in self.poses],
            "techniques": [t.to_dict() for t in self.techniques],
            "synthesis": self.synthesis,
        }
