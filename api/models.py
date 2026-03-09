"""API response models."""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class VideoResponse(BaseModel):
    video_id: str
    filename: str
    message: str


class TechniqueDetail(BaseModel):
    name: str
    japanese_name: str
    category: str
    execution_score: int
    kuzushi_rating: int
    tsukuri_rating: int
    kake_rating: int
    score_result: str
    biomechanics_notes: str
    strengths: List[str]
    improvements: List[str]
    drill_recommendations: List[str]
    timestamp_start: float
    timestamp_end: float


class AnalysisResult(BaseModel):
    video_id: str
    status: str  # "pending", "completed", "error"
    analysis: Optional[Dict[str, Any]] = None
    report_text: Optional[str] = None
    error: Optional[str] = None


class AnalysisSummary(BaseModel):
    video_id: str
    status: str
    overall_assessment: Optional[str] = None
    techniques_count: int = 0
    moments_count: int = 0
    dominant_techniques: Optional[List[str]] = None
    priority_improvements: Optional[List[str]] = None
