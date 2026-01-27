from pydantic import BaseModel
from typing import Optional

class VideoResponse(BaseModel):
    video_id: str
    filename: str
    message: str

class AnalysisResult(BaseModel):
    video_id: str
    status: str
    analysis: Optional[str] = None
    file_path: Optional[str] = None
    error: Optional[str] = None
